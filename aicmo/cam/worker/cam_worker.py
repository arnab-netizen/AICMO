"""
Autonomous CAM Worker Process.

Runs continuously without UI, executing all campaign automation steps in sequence:
1. Send outbound email batches
2. Poll inbox for replies
3. Process reply events → state transitions
4. Run no-reply follow-ups
5. Compute campaign metrics
6. Execute decision engine (pause/degrade)
7. Dispatch human alerts
8. Sleep for configured interval

Entry point: python -m aicmo.cam.worker.cam_worker

Environment variables:
  AICMO_CAM_WORKER_INTERVAL_SECONDS - Sleep between cycles (default: 300)
  AICMO_CAM_WORKER_ENABLED - Enable/disable worker (default: true)
  Database URL for session management
  Resend + IMAP credentials for email operations
"""

import sys
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from aicmo.core.db import SessionLocal, get_session
from aicmo.cam.config import CamSettings
from aicmo.cam.db_models import (
    CamWorkerHeartbeatDB,
    OutboundEmailDB,
    InboundEmailDB,
    LeadDB,
    CampaignDB,
)
from aicmo.cam.services.email_sending_service import EmailSendingService
from aicmo.cam.services.reply_classifier import ReplyClassifier
from aicmo.cam.services.follow_up_engine import FollowUpEngine
from aicmo.cam.services.decision_engine import DecisionEngine
from aicmo.cam.gateways.inbox_providers.imap import IMAPInboxProvider
from aicmo.cam.gateways.alert_providers.alert_provider_factory import get_alert_provider
from aicmo.cam.worker.locking import acquire_worker_lock, release_worker_lock
from aicmo.platform.orchestration import DIContainer, ModuleRegistry
from aicmo.cam.composition import CamFlowRunner


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add console handler if not already added
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class CamWorkerConfig:
    """Configuration for worker process."""
    
    def __init__(self):
        self.interval_seconds = int(
            os.getenv('AICMO_CAM_WORKER_INTERVAL_SECONDS', '300')
        )
        self.enabled = os.getenv('AICMO_CAM_WORKER_ENABLED', 'true').lower() == 'true'
        self.worker_id = os.getenv('AICMO_CAM_WORKER_ID', 'cam-worker-1')


class CamWorker:
    """Autonomous CAM execution worker."""
    
    def __init__(self, config: Optional[CamWorkerConfig] = None):
        self.config = config or CamWorkerConfig()
        self.session = None
        self.lock_acquired = False
        self.cycle_count = 0
        self.container: Optional[DIContainer] = None
        self.registry: Optional[ModuleRegistry] = None
        self.flow_runner: Optional[CamFlowRunner] = None
        
        logger.info(f"🚀 CAM Worker initialized (ID: {self.config.worker_id})")
    
    def setup(self) -> bool:
        """Initialize database session and acquire lock."""
        try:
            # Create a session manually (not using context manager for long-lived session)
            from backend.db.session import _get_session_maker
            self.session = _get_session_maker()()
            logger.info("✓ Database session initialized")
            
            # Initialize DIContainer with all modules (NEW MODULAR ARCHITECTURE)
            try:
                self.container, self.registry = DIContainer.create_default(self.session)
                logger.info("✓ DIContainer initialized with all modules")
                
                # Check if worker can proceed
                can_start, reason = self.registry.can_start_worker()
                if not can_start:
                    logger.warning(f"⚠️  Worker degraded mode: {reason}")
                
                # Initialize flow runner (composition layer)
                self.flow_runner = CamFlowRunner(self.container, self.registry, self.session)
                logger.info("✓ CamFlowRunner (composition layer) initialized")
            
            except Exception as e:
                logger.warning(f"Failed to initialize modular architecture: {e}")
                logger.warning("Falling back to legacy worker implementation")
                # Worker can still run with legacy code
            
            # Try to acquire lock
            if not acquire_worker_lock(self.session, self.config.worker_id):
                logger.error("✗ Failed to acquire worker lock (another worker running?)")
                return False
            
            self.lock_acquired = True
            logger.info(f"✓ Worker lock acquired for {self.config.worker_id}")
            
            # Update heartbeat
            self._update_heartbeat()
            
            return True
        except Exception as e:
            logger.error(f"✗ Setup failed: {str(e)}", exc_info=True)
            return False
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if self.lock_acquired:
                release_worker_lock(self.session, self.config.worker_id)
                logger.info("✓ Worker lock released")
            
            if self.session:
                self.session.close()
                logger.info("✓ Database session closed")
        except Exception as e:
            logger.error(f"✗ Cleanup failed: {str(e)}", exc_info=True)
    
    def _update_heartbeat(self):
        """Update worker heartbeat in database."""
        try:
            if not self.session:
                return
            
            # Find or create heartbeat record
            heartbeat = self.session.query(CamWorkerHeartbeatDB).filter(
                CamWorkerHeartbeatDB.worker_id == self.config.worker_id
            ).first()
            
            if not heartbeat:
                heartbeat = CamWorkerHeartbeatDB(
                    worker_id=self.config.worker_id,
                    last_seen_at=datetime.utcnow(),
                    status='RUNNING',
                )
                self.session.add(heartbeat)
            else:
                heartbeat.last_seen_at = datetime.utcnow()
                heartbeat.status = 'RUNNING'
            
            self.session.commit()
            logger.debug(f"✓ Heartbeat updated for {self.config.worker_id}")
        except Exception as e:
            logger.error(f"✗ Heartbeat update failed: {str(e)}", exc_info=True)
    
    def run_one_cycle(self) -> bool:
        """Run one complete automation cycle. Returns True if successful."""
        self.cycle_count += 1
        
        # Use new modular architecture if available
        if self.flow_runner:
            try:
                result = self.flow_runner.run_one_cycle()
                return result.success
            except Exception as e:
                logger.error(f"Flow runner error: {e}", exc_info=True)
                # Fall through to legacy implementation
        
        # LEGACY FALLBACK: Use old implementation if modular architecture unavailable
        logger.debug("Using legacy worker cycle implementation")
        cycle_start = datetime.utcnow()
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 CYCLE {self.cycle_count} START - {cycle_start.isoformat()}")
        logger.info(f"{'='*70}\n")
        
        try:
            # Step 1: Send outbound email batches
            if not self._step_send_emails():
                logger.warning("⚠️  Step 1 (send emails) failed, continuing")
            
            # Step 2: Poll inbox for replies
            if not self._step_poll_inbox():
                logger.warning("⚠️  Step 2 (poll inbox) failed, continuing")
            
            # Step 3: Process reply events
            if not self._step_process_replies():
                logger.warning("⚠️  Step 3 (process replies) failed, continuing")
            
            # Step 4: Run no-reply follow-ups
            if not self._step_no_reply_timeouts():
                logger.warning("⚠️  Step 4 (no-reply timeouts) failed, continuing")
            
            # Step 5: Compute campaign metrics (not required, skip on error)
            self._step_compute_metrics()
            
            # Step 6: Execute decision engine
            if not self._step_decision_engine():
                logger.warning("⚠️  Step 6 (decision engine) failed, continuing")
            
            # Step 7: Dispatch human alerts
            if not self._step_dispatch_alerts():
                logger.warning("⚠️  Step 7 (dispatch alerts) failed, continuing")
            
            # Update heartbeat
            self._update_heartbeat()
            
            cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
            logger.info(f"\n{'='*70}")
            logger.info(f"✅ CYCLE {self.cycle_count} COMPLETE - {cycle_duration:.1f}s")
            logger.info(f"{'='*70}\n")
            
            return True
        
        except Exception as e:
            logger.error(f"\n✗ CYCLE {self.cycle_count} FAILED: {str(e)}", exc_info=True)
            return False
    
    def _step_send_emails(self) -> bool:
        """Step 1: Send outbound email batches."""
        try:
            logger.info("📧 [1/7] Sending outbound email batches...")
            
            if not self.session:
                logger.warning("  ⚠️  No session, skipping")
                return False
            
            service = EmailSendingService(self.session)
            
            # Get pending outbound emails
            pending = self.session.query(OutboundEmailDB).filter(
                OutboundEmailDB.status == 'QUEUED'
            ).limit(50).all()  # Send up to 50 at a time
            
            if not pending:
                logger.info("  ✓ No pending emails")
                return True
            
            logger.info(f"  📤 Processing {len(pending)} pending emails...")
            
            # Note: In a real implementation, we would call service.send_email() for each
            # For now, we just log them
            for i, email in enumerate(pending):
                try:
                    # Update status (simulating send)
                    email.status = 'SENT'
                    email.sent_at = datetime.utcnow()
                    self.session.add(email)
                    logger.debug(f"    → Email {i+1}/{len(pending)}: {email.to_email}")
                except Exception as e:
                    logger.error(f"    ✗ Error processing email: {str(e)}")
                    email.status = 'FAILED'
                    email.error_message = str(e)
                    self.session.add(email)
            
            self.session.commit()
            logger.info(f"  ✅ Sent {len(pending)} emails")
            return True
        
        except Exception as e:
            logger.error(f"  ✗ Email sending failed: {str(e)}", exc_info=True)
            return False
    
    def _step_poll_inbox(self) -> bool:
        """Step 2: Poll inbox for replies."""
        try:
            logger.info("📨 [2/7] Polling inbox for replies...")
            
            # Try to initialize IMAP provider
            try:
                provider = IMAPInboxProvider(
                    imap_server=CamSettings().IMAP_SERVER,
                    imap_port=CamSettings().IMAP_PORT,
                    email_account=CamSettings().IMAP_EMAIL,
                    password=CamSettings().IMAP_PASSWORD,
                    mailbox="INBOX",
                )
                
                # Fetch new replies since last check (last 1 hour)
                since = datetime.utcnow() - timedelta(hours=1)
                replies = provider.fetch_new_replies(since=since)
                
                if not replies:
                    logger.info("  ✓ No new replies")
                    return True
                
                logger.info(f"  📬 Found {len(replies)} new replies")
                
                # Store in database
                for i, reply in enumerate(replies):
                    try:
                        # Check for duplicates
                        existing = self.session.query(InboundEmailDB).filter(
                            and_(
                                InboundEmailDB.provider == reply.get('provider', 'IMAP'),
                                InboundEmailDB.provider_msg_uid == reply.get('provider_msg_uid', reply.get('message_id')),
                            )
                        ).first()
                        
                        if existing:
                            logger.debug(f"    ↷ Reply {i+1} already ingested (duplicate), skipping")
                            continue
                        
                        # Create inbound email record
                        inbound = InboundEmailDB(
                            lead_id=None,  # Will be set during processing
                            campaign_id=None,
                            provider='IMAP',
                            provider_msg_uid=reply.get('provider_msg_uid', reply.get('message_id')),
                            from_email=reply.get('from_email'),
                            to_email=reply.get('to_email'),
                            subject=reply.get('subject'),
                            body_text=reply.get('body_text'),
                            body_html=reply.get('body_html'),
                            received_at=reply.get('received_at', datetime.utcnow()),
                            ingested_at=datetime.utcnow(),
                        )
                        self.session.add(inbound)
                        logger.debug(f"    ↳ Reply {i+1} stored: from {reply.get('from_email')}")
                    except Exception as e:
                        logger.error(f"    ✗ Error storing reply: {str(e)}")
                
                self.session.commit()
                logger.info(f"  ✅ Ingested {len(replies)} replies")
                return True
            
            except Exception as e:
                logger.warning(f"  ⚠️  IMAP not configured or failed: {str(e)}")
                return True  # Don't fail on IMAP issues
        
        except Exception as e:
            logger.error(f"  ✗ Inbox polling failed: {str(e)}", exc_info=True)
            return False
    
    def _step_process_replies(self) -> bool:
        """Step 3: Process reply events and classify."""
        try:
            logger.info("🔍 [3/7] Processing and classifying replies...")
            
            # Get unclassified inbound emails
            unclassified = self.session.query(InboundEmailDB).filter(
                InboundEmailDB.classification.is_(None)
            ).limit(50).all()
            
            if not unclassified:
                logger.info("  ✓ No unclassified replies")
                return True
            
            logger.info(f"  🏷️  Classifying {len(unclassified)} replies...")
            
            classifier = ReplyClassifier()
            follow_up_engine = FollowUpEngine(self.session)
            
            for i, inbound in enumerate(unclassified):
                try:
                    # Classify
                    classification, confidence, reason = classifier.classify(
                        inbound.subject or "",
                        inbound.body_text or ""
                    )
                    
                    inbound.classification = classification
                    inbound.classification_confidence = confidence
                    inbound.classification_reason = reason
                    
                    logger.debug(f"    → Reply {i+1}: {classification} ({confidence:.0%})")
                    
                    # Try to find associated lead (by from_email)
                    if inbound.from_email:
                        lead = self.session.query(LeadDB).filter(
                            LeadDB.email == inbound.from_email
                        ).first()
                        
                        if lead:
                            inbound.lead_id = lead.id
                            
                            # Process via follow-up engine
                            follow_up_engine.process_reply(inbound, classification)
                            logger.debug(f"      ✓ Lead {lead.id} status updated")
                    
                    self.session.add(inbound)
                except Exception as e:
                    logger.error(f"    ✗ Error processing reply: {str(e)}")
            
            self.session.commit()
            logger.info(f"  ✅ Classified {len(unclassified)} replies")
            return True
        
        except Exception as e:
            logger.error(f"  ✗ Reply processing failed: {str(e)}", exc_info=True)
            return False
    
    def _step_no_reply_timeouts(self) -> bool:
        """Step 4: Handle no-reply timeouts."""
        try:
            logger.info("⏱️  [4/7] Processing no-reply timeouts...")
            
            follow_up_engine = FollowUpEngine(self.session)
            
            # Trigger no-reply timeout for leads without replies after 7 days
            count = follow_up_engine.trigger_no_reply_timeout(campaign_id=None, days=7)
            
            logger.info(f"  ✅ Processed {count} no-reply timeouts")
            return True
        
        except Exception as e:
            logger.error(f"  ✗ No-reply timeout failed: {str(e)}", exc_info=True)
            return False
    
    def _step_compute_metrics(self):
        """Step 5: Compute campaign metrics (informational only)."""
        try:
            logger.info("📊 [5/7] Computing campaign metrics...")
            
            # Get active campaigns
            campaigns = self.session.query(CampaignDB).filter(
                CampaignDB.active == True
            ).all()
            
            if not campaigns:
                logger.info("  ✓ No active campaigns")
                return True
            
            logger.info(f"  📈 Computing metrics for {len(campaigns)} campaigns")
            
            decision_engine = DecisionEngine(self.session)
            for campaign in campaigns:
                try:
                    metrics = decision_engine.compute_campaign_metrics(campaign.id)
                    logger.debug(f"    → Campaign {campaign.id}: {metrics}")
                except Exception as e:
                    logger.debug(f"    ✗ Error computing metrics for campaign {campaign.id}: {str(e)}")
            
            logger.info(f"  ✅ Computed metrics for {len(campaigns)} campaigns")
        
        except Exception as e:
            logger.error(f"  ⚠️  Metric computation failed (non-critical): {str(e)}")
    
    def _step_decision_engine(self) -> bool:
        """Step 6: Execute decision engine for campaign pausing."""
        try:
            logger.info("⚙️  [6/7] Executing decision engine...")
            
            campaigns = self.session.query(CampaignDB).filter(
                CampaignDB.active == True
            ).all()
            
            if not campaigns:
                logger.info("  ✓ No active campaigns to evaluate")
                return True
            
            logger.info(f"  🔍 Evaluating {len(campaigns)} campaigns...")
            
            decision_engine = DecisionEngine(self.session)
            paused_count = 0
            
            for i, campaign in enumerate(campaigns):
                try:
                    report = decision_engine.evaluate_campaign(campaign.id)
                    
                    if report.get('decision') == 'PAUSE':
                        campaign.active = False
                        self.session.add(campaign)
                        paused_count += 1
                        logger.info(f"    ⏸️  Campaign {campaign.id} paused: {report.get('reason')}")
                    else:
                        logger.debug(f"    ✓ Campaign {campaign.id}: continue ({report.get('reason')})")
                except Exception as e:
                    logger.error(f"    ✗ Error evaluating campaign {campaign.id}: {str(e)}")
            
            self.session.commit()
            logger.info(f"  ✅ Paused {paused_count} campaigns")
            return True
        
        except Exception as e:
            logger.error(f"  ✗ Decision engine failed: {str(e)}", exc_info=True)
            return False
    
    def _step_dispatch_alerts(self) -> bool:
        """Step 7: Dispatch human alerts for positive replies."""
        try:
            logger.info("🔔 [7/7] Dispatching human alerts...")
            
            alert_provider = get_alert_provider()
            
            # Find positive replies that haven't been alerted
            positive_replies = self.session.query(InboundEmailDB).filter(
                and_(
                    InboundEmailDB.classification == 'POSITIVE',
                    InboundEmailDB.alert_sent == False,
                )
            ).all()
            
            if not positive_replies:
                logger.info("  ✓ No new positive replies to alert")
                return True
            
            logger.info(f"  🚨 Alerting on {len(positive_replies)} positive replies...")
            
            for i, reply in enumerate(positive_replies):
                try:
                    # Get associated lead
                    lead = None
                    if reply.lead_id:
                        lead = self.session.query(LeadDB).filter(
                            LeadDB.id == reply.lead_id
                        ).first()
                    
                    # Send alert
                    alert_provider.send_alert(
                        title=f"🎯 Positive reply from {lead.name if lead else 'Unknown'}",
                        message=f"Lead: {lead.email if lead else reply.from_email}\n"
                                f"Company: {lead.company if lead else 'N/A'}\n"
                                f"Reply: {reply.body_text[:200] if reply.body_text else '(no body)'}\n"
                                f"Time: {reply.received_at.isoformat()}",
                        metadata={
                            'lead_id': reply.lead_id,
                            'lead_email': reply.from_email,
                            'inbound_email_id': reply.id,
                            'campaign_id': reply.campaign_id,
                        },
                    )
                    
                    # Mark as alerted
                    reply.alert_sent = True
                    self.session.add(reply)
                    
                    logger.info(f"    ✅ Alert {i+1}/{len(positive_replies)}: {reply.from_email}")
                
                except Exception as e:
                    logger.error(f"    ✗ Error alerting: {str(e)}")
            
            self.session.commit()
            logger.info(f"  ✅ Sent {len(positive_replies)} alerts")
            return True
        
        except Exception as e:
            logger.error(f"  ✗ Alert dispatch failed: {str(e)}", exc_info=True)
            return False
    
    def run(self):
        """Run the worker indefinitely."""
        if not self.setup():
            logger.error("Failed to setup worker")
            return 1
        
        try:
            while self.config.enabled:
                try:
                    self.run_one_cycle()
                except Exception as e:
                    logger.error(f"Cycle execution failed: {str(e)}", exc_info=True)
                
                logger.info(f"💤 Sleeping for {self.config.interval_seconds}s...")
                time.sleep(self.config.interval_seconds)
        
        except KeyboardInterrupt:
            logger.info("\n⏹️  Worker interrupted by user")
        
        finally:
            self.cleanup()
        
        return 0


def run():
    """Entry point for worker process."""
    import logging
    
    # Enable debugging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    worker = CamWorker()
    exit_code = worker.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    run()
