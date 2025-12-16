"""
Campaign Orchestrator Engine.

Core execution loop that:
1. Claims campaign with lease
2. Selects eligible leads
3. Chooses messages
4. Creates dispatch jobs
5. Records outcomes
6. Advances lead state

Production-safe with:
- Single-writer guarantee (lease)
- Per-lead transactions
- Idempotency enforcement
- DNC/suppression/unsubscribe checks
- Kill switch + pause enforcement
- Retry scheduling with backoff
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import and_

from aicmo.cam.db_models import CampaignDB, LeadDB, LeadStatus
from aicmo.venture.models import CampaignConfigDB, CampaignStatus
from aicmo.venture.distribution_models import DistributionJobDB
from aicmo.venture.audit import log_audit
from aicmo.cam.engine.safety_limits import can_send_email, remaining_email_quota

from aicmo.cam.orchestrator.models import RunStatus
from aicmo.cam.orchestrator.repositories import (
    UnsubscribeRepository,
    SuppressionRepository,
    OrchestratorRunRepository,
)
from aicmo.cam.orchestrator.narrative_selector import NarrativeSelector
from aicmo.cam.orchestrator.adapters import ProofEmailSenderAdapter
from aicmo.gateways.interfaces import EmailSender


@dataclass
class OrchestratorTickResult:
    """Result of one orchestrator tick."""
    leads_processed: int
    jobs_created: int
    attempts_succeeded: int
    attempts_failed: int
    skipped_dnc: int
    skipped_unsubscribed: int
    skipped_suppressed: int
    skipped_quota: int
    skipped_idempotent: int
    errors: List[str]


class CampaignOrchestrator:
    """
    Campaign orchestrator engine.
    
    Executes continuous campaign loop with safety guarantees.
    """
    
    # Constants
    MAX_LEADS_PER_TICK = 25
    MAX_STEPS_PER_LEAD = 3
    COOLDOWN_MINUTES = 1440  # 24 hours between touches
    LEASE_DURATION = timedelta(minutes=5)
    RETRY_BACKOFF_BASE = 300  # 5 minutes base backoff
    
    def __init__(
        self,
        session: Session,
        email_sender: Optional[EmailSender] = None,
        mode: str = "proof",
    ):
        self.session = session
        self.mode = mode
        
        # Adapter selection
        if email_sender:
            self.email_sender = email_sender
        elif mode == "proof":
            self.email_sender = ProofEmailSenderAdapter()
        else:
            raise ValueError("Live mode requires email_sender parameter")
        
        # Repositories
        self.unsub_repo = UnsubscribeRepository(session)
        self.suppression_repo = SuppressionRepository(session)
        self.run_repo = OrchestratorRunRepository(session)
        
        # Selector
        self.narrative_selector = NarrativeSelector(session)
        
        # Worker ID
        self.worker_id = f"orchestrator_{uuid.uuid4().hex[:8]}"
    
    def tick(
        self,
        campaign_id: int,
        now: datetime,
        batch_size: Optional[int] = None,
    ) -> OrchestratorTickResult:
        """
        Execute one tick of campaign orchestration.
        
        Args:
            campaign_id: Campaign to execute
            now: Current timestamp
            batch_size: Max leads to process (default MAX_LEADS_PER_TICK)
            
        Returns:
            OrchestratorTickResult with counts and errors
        """
        result = OrchestratorTickResult(
            leads_processed=0,
            jobs_created=0,
            attempts_succeeded=0,
            attempts_failed=0,
            skipped_dnc=0,
            skipped_unsubscribed=0,
            skipped_suppressed=0,
            skipped_quota=0,
            skipped_idempotent=0,
            errors=[],
        )
        
        batch_size = batch_size or self.MAX_LEADS_PER_TICK
        
        # Step 1: Try to claim campaign
        run = self.run_repo.try_claim_campaign(
            campaign_id=campaign_id,
            worker_id=self.worker_id,
            lease_duration=self.LEASE_DURATION,
            now=now,
        )
        
        if not run:
            result.errors.append("Campaign already claimed by another worker")
            return result
        
        try:
            # Step 2: Validate campaign
            campaign, config = self._validate_campaign(campaign_id)
            if not campaign or not config:
                result.errors.append("Campaign validation failed")
                self.run_repo.mark_completed(run.id, now, RunStatus.FAILED, "Campaign not found or invalid")
                return result
            
            # Step 3: Check pause/kill switch
            if config.status != CampaignStatus.RUNNING:
                result.errors.append(f"Campaign status: {config.status.value}")
                self.run_repo.mark_completed(run.id, now, RunStatus.STOPPED, f"Campaign {config.status.value}")
                return result
            
            if config.kill_switch:
                result.errors.append("Kill switch activated")
                self.run_repo.mark_completed(run.id, now, RunStatus.STOPPED, "Kill switch")
                return result
            
            # Step 4: Check quota
            quota = remaining_email_quota(self.session, campaign_id, now)
            if quota <= 0:
                result.errors.append("Daily quota exhausted")
                result.skipped_quota = batch_size
                self.run_repo.mark_completed(run.id, now, RunStatus.COMPLETED, "Quota exhausted")
                return result
            
            # Limit batch to available quota
            batch_size = min(batch_size, quota)
            
            # Step 5: Select eligible leads
            eligible_leads = self._select_eligible_leads(
                campaign_id=campaign_id,
                now=now,
                limit=batch_size,
            )
            
            if not eligible_leads:
                # No work to do
                self.run_repo.mark_completed(run.id, now, RunStatus.COMPLETED, "No eligible leads")
                return result
            
            # Step 6: Process each lead (per-lead transaction boundary)
            for lead in eligible_leads:
                try:
                    # Re-check kill switch before each dispatch
                    self.session.refresh(config)
                    if config.kill_switch or config.status != CampaignStatus.RUNNING:
                        result.errors.append("Campaign stopped mid-tick")
                        break
                    
                    lead_result = self._process_lead(
                        campaign_id=campaign_id,
                        lead=lead,
                        now=now,
                    )
                    
                    # Aggregate results
                    if lead_result["skipped_dnc"]:
                        result.skipped_dnc += 1
                    elif lead_result["skipped_unsubscribed"]:
                        result.skipped_unsubscribed += 1
                    elif lead_result["skipped_suppressed"]:
                        result.skipped_suppressed += 1
                    elif lead_result["skipped_idempotent"]:
                        result.skipped_idempotent += 1
                    elif lead_result["job_created"]:
                        result.jobs_created += 1
                        if lead_result["attempt_succeeded"]:
                            result.attempts_succeeded += 1
                        else:
                            result.attempts_failed += 1
                    
                    result.leads_processed += 1
                    
                    # Commit per-lead transaction
                    self.session.commit()
                    
                except Exception as e:
                    # Rollback lead transaction
                    self.session.rollback()
                    result.errors.append(f"Lead {lead.id} error: {str(e)}")
                    result.attempts_failed += 1
            
            # Step 7: Update run progress
            self.run_repo.update_progress(
                run_id=run.id,
                leads_processed=result.leads_processed,
                jobs_created=result.jobs_created,
                attempts_succeeded=result.attempts_succeeded,
                attempts_failed=result.attempts_failed,
            )
            
            # Step 8: Mark run completed
            self.run_repo.mark_completed(run.id, now, RunStatus.COMPLETED)
            self.session.commit()
            
        except Exception as e:
            self.session.rollback()
            result.errors.append(f"Tick error: {str(e)}")
            self.run_repo.mark_completed(run.id, now, RunStatus.FAILED, str(e))
        
        return result
    
    def _validate_campaign(
        self,
        campaign_id: int,
    ) -> tuple[Optional[CampaignDB], Optional[CampaignConfigDB]]:
        """Validate campaign exists and has config."""
        campaign = self.session.query(CampaignDB).filter_by(id=campaign_id).first()
        if not campaign:
            return None, None
        
        config = self.session.query(CampaignConfigDB).filter_by(campaign_id=campaign_id).first()
        if not config:
            return None, None
        
        return campaign, config
    
    def _select_eligible_leads(
        self,
        campaign_id: int,
        now: datetime,
        limit: int,
    ) -> List[LeadDB]:
        """
        Select leads eligible for next outreach.
        
        Eligibility:
        - consent_status != DNC
        - status in [NEW, CONTACTED]
        - next_action_at <= now (or NULL for NEW leads)
        - Not exhausted step limit
        """
        return (
            self.session.query(LeadDB)
            .filter(
                and_(
                    LeadDB.campaign_id == campaign_id,
                    LeadDB.consent_status != "DNC",
                    LeadDB.status.in_([LeadStatus.NEW, LeadStatus.CONTACTED]),
                    or_(
                        LeadDB.next_action_at == None,
                        LeadDB.next_action_at <= now,
                    ),
                )
            )
            .limit(limit)
            .all()
        )
    
    def _process_lead(
        self,
        campaign_id: int,
        lead: LeadDB,
        now: datetime,
    ) -> dict:
        """
        Process one lead (within transaction).
        
        Returns dict with skip reasons and success flags.
        """
        result = {
            "skipped_dnc": False,
            "skipped_unsubscribed": False,
            "skipped_suppressed": False,
            "skipped_idempotent": False,
            "job_created": False,
            "attempt_succeeded": False,
        }
        
        # Safety checks
        if lead.consent_status == "DNC":
            result["skipped_dnc"] = True
            log_audit(self.session, "lead", str(lead.id), "SKIP_DNC", "orchestrator")
            return result
        
        if lead.email and self.unsub_repo.is_unsubscribed(lead.email):
            result["skipped_unsubscribed"] = True
            log_audit(self.session, "lead", str(lead.id), "SKIP_UNSUBSCRIBED", "orchestrator")
            return result
        
        if self.suppression_repo.is_suppressed(
            email=lead.email,
            identity_hash=lead.identity_hash,
        ):
            result["skipped_suppressed"] = True
            log_audit(self.session, "lead", str(lead.id), "SKIP_SUPPRESSED", "orchestrator")
            return result
        
        # Determine step index
        step_index = self._calculate_step_index(lead)
        
        if step_index >= self.MAX_STEPS_PER_LEAD:
            # Exhausted sequence
            lead.status = LeadStatus.LOST
            log_audit(self.session, "lead", str(lead.id), "SEQUENCE_EXHAUSTED", "orchestrator")
            return result
        
        # Choose message
        message_choice = self.narrative_selector.choose_message(
            campaign_id=campaign_id,
            lead=lead,
            step_index=step_index,
        )
        
        # Generate idempotency key
        idempotency_key = f"{campaign_id}:{lead.id}:{message_choice.message_id}:{step_index}"
        
        # Check idempotency
        existing_job = (
            self.session.query(DistributionJobDB)
            .filter_by(idempotency_key=idempotency_key)
            .first()
        )
        
        if existing_job:
            result["skipped_idempotent"] = True
            log_audit(self.session, "lead", str(lead.id), "SKIP_IDEMPOTENT", "orchestrator", {"job_id": existing_job.id})
            return result
        
        # Create distribution job
        job = DistributionJobDB(
            venture_id=lead.venture_id,
            campaign_id=campaign_id,
            lead_id=lead.id,
            channel="email",
            status="PENDING",
            idempotency_key=idempotency_key,
            step_index=step_index,
            retry_count=0,
            max_retries=3,
        )
        self.session.add(job)
        self.session.flush()
        
        result["job_created"] = True
        
        # Execute dispatch (proof or live)
        success = self._execute_dispatch(job, lead, message_choice, now)
        
        if success:
            result["attempt_succeeded"] = True
            job.status = "SENT" if self.mode == "live" else "SENT_PROOF"
            job.executed_at = now
            
            # Update lead state
            lead.last_contacted_at = now
            lead.status = LeadStatus.CONTACTED
            lead.next_action_at = now + timedelta(minutes=self.COOLDOWN_MINUTES)
            
            # Append engagement note
            note = f"[{now.isoformat()}] Sent {message_choice.message_id} (step {step_index})"
            if lead.engagement_notes:
                lead.engagement_notes += f"\n{note}"
            else:
                lead.engagement_notes = note
            
            log_audit(
                self.session,
                "distribution_job",
                str(job.id),
                "DISPATCHED",
                "orchestrator",
                {"message_id": message_choice.message_id, "step": step_index},
            )
        else:
            result["attempt_succeeded"] = False
            job.status = "FAILED"
            
            # Schedule retry with backoff
            job.retry_count += 1
            if job.retry_count < job.max_retries:
                backoff_seconds = self.RETRY_BACKOFF_BASE * (2 ** job.retry_count)
                job.next_retry_at = now + timedelta(seconds=backoff_seconds)
                job.status = "RETRY_SCHEDULED"
            else:
                job.status = "FAILED_PERMANENT"
            
            log_audit(
                self.session,
                "distribution_job",
                str(job.id),
                "DISPATCH_FAILED",
                "orchestrator",
                {"retry_count": job.retry_count},
            )
        
        return result
    
    def _calculate_step_index(self, lead: LeadDB) -> int:
        """Calculate which step in sequence lead is on."""
        # Count successful distributions to this lead
        count = (
            self.session.query(DistributionJobDB)
            .filter(
                and_(
                    DistributionJobDB.lead_id == lead.id,
                    DistributionJobDB.status.in_(["SENT", "SENT_PROOF"]),
                )
            )
            .count()
        )
        return count
    
    def _execute_dispatch(
        self,
        job: DistributionJobDB,
        lead: LeadDB,
        message_choice,
        now: datetime,
    ) -> bool:
        """
        Execute dispatch (proof or live).
        
        Returns True on success, False on failure.
        """
        try:
            if not lead.email:
                job.error = "Lead has no email address"
                return False
            
            # TODO: Load actual message content from template registry
            # For MVP, use placeholder content
            subject = f"Message: {message_choice.message_id}"
            body = f"<p>This is {message_choice.message_id} for {lead.name or 'you'}</p>"
            
            # Call adapter
            import asyncio
            result = asyncio.run(
                self.email_sender.send_email(
                    to_email=lead.email,
                    subject=subject,
                    html_body=body,
                    metadata={
                        "campaign_id": job.campaign_id,
                        "lead_id": lead.id,
                        "message_id": message_choice.message_id,
                        "idempotency_key": job.idempotency_key,
                    },
                )
            )
            
            from aicmo.domain.execution import ExecutionStatus
            
            if result.status == ExecutionStatus.SUCCESS:
                # Store provider message ID
                job.message_id = result.platform_post_id
                return True
            else:
                job.error = result.error_message or "Unknown error"
                return False
                
        except Exception as e:
            job.error = str(e)
            return False


def or_(*args):
    """SQLAlchemy or_ helper (import at module level causes issues)."""
    from sqlalchemy import or_ as sqlalchemy_or
    return sqlalchemy_or(*args)
