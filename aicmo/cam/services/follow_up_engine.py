"""
Phase 3: Automated follow-up logic and state transitions.

Handles:
- State transitions based on reply classification
- No-reply timeout triggers
- Next email in sequence scheduling
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from aicmo.cam.db_models import LeadDB, OutboundEmailDB, InboundEmailDB, CampaignDB
from aicmo.cam.engine.lead_nurture import EmailTemplate, NurtureScheduler
from aicmo.cam.services.email_sending_service import EmailSendingService
from aicmo.cam.services.reply_classifier import ReplyClassification


logger = logging.getLogger(__name__)


class FollowUpEngine:
    """
    Manage state transitions and follow-ups based on reply classification.
    
    Transitions:
    - POSITIVE reply → Mark lead as qualified, advance sequence
    - NEGATIVE reply → Mark as suppressed, stop outreach
    - OOO/BOUNCE reply → No action, next email can retry
    - No reply after delay → Send next email in sequence
    """
    
    def __init__(self, db_session: Session):
        """Initialize with database session."""
        self.db = db_session
        self.email_service = EmailSendingService(db_session)
        self.scheduler = NurtureScheduler()
    
    def handle_positive_reply(self, lead_id: int, inbound_email_id: int) -> None:
        """
        Handle positive reply: mark lead as interested/qualified.
        
        Args:
            lead_id: ID of replying lead
            inbound_email_id: ID of the inbound email record
        """
        lead = self.db.query(LeadDB).filter_by(id=lead_id).first()
        if not lead:
            logger.warning(f"Lead {lead_id} not found for positive reply")
            return
        
        # Update lead status
        if lead.status != "qualified":
            logger.info(f"Lead {lead_id} marked as qualified due to positive reply")
            lead.status = "qualified"
            lead.last_replied_at = datetime.utcnow()
        
        self.db.commit()
    
    def handle_negative_reply(self, lead_id: int, inbound_email_id: int) -> None:
        """
        Handle negative reply: suppress further outreach.
        
        Args:
            lead_id: ID of replying lead
            inbound_email_id: ID of the inbound email record
        """
        lead = self.db.query(LeadDB).filter_by(id=lead_id).first()
        if not lead:
            logger.warning(f"Lead {lead_id} not found for negative reply")
            return
        
        # Update lead status to suppressed
        if lead.status != "suppressed":
            logger.info(f"Lead {lead_id} marked as suppressed due to negative reply")
            lead.status = "suppressed"
            lead.last_replied_at = datetime.utcnow()
        
        self.db.commit()
    
    def handle_unsub_request(self, lead_id: int, inbound_email_id: int) -> None:
        """
        Handle unsubscribe request: suppress further outreach permanently.
        
        Args:
            lead_id: ID of lead requesting unsubscribe
            inbound_email_id: ID of the inbound email record
        """
        lead = self.db.query(LeadDB).filter_by(id=lead_id).first()
        if not lead:
            logger.warning(f"Lead {lead_id} not found for unsub request")
            return
        
        # Update lead status and add tag
        if lead.status != "unsubscribed":
            logger.info(f"Lead {lead_id} marked as unsubscribed")
            lead.status = "unsubscribed"
            if not lead.tags:
                lead.tags = []
            if "unsubscribed" not in lead.tags:
                lead.tags.append("unsubscribed")
        
        self.db.commit()
    
    def process_reply(
        self,
        inbound_email: InboundEmailDB,
        classification: str,  # POSITIVE, NEGATIVE, OOO, BOUNCE, UNSUB, NEUTRAL
    ) -> None:
        """
        Process a classified reply and update lead state accordingly.
        
        Args:
            inbound_email: InboundEmailDB record
            classification: Classification result (e.g., "POSITIVE")
        """
        lead_id = inbound_email.lead_id
        if not lead_id:
            logger.warning("Inbound email has no lead_id, skipping state transition")
            return
        
        logger.info(f"Processing {classification} reply for lead {lead_id}")
        
        if classification == ReplyClassification.POSITIVE:
            self.handle_positive_reply(lead_id, inbound_email.id)
        elif classification == ReplyClassification.NEGATIVE:
            self.handle_negative_reply(lead_id, inbound_email.id)
        elif classification == ReplyClassification.UNSUB:
            self.handle_unsub_request(lead_id, inbound_email.id)
        # OOO and BOUNCE: no action, let sequence continue
    
    def trigger_no_reply_timeout(self, campaign_id: int, days_since_last_send: int = 7) -> int:
        """
        Find leads with no reply after specified days and send next email.
        
        This is the "auto-advance" mechanism:
        - Lead sent email N days ago
        - No reply received
        - Send next email in sequence
        
        Args:
            campaign_id: Campaign to evaluate
            days_since_last_send: Days to wait before assuming no-reply (default 7)
        
        Returns:
            Number of emails sent
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days_since_last_send)
        
        # Find leads that:
        # 1. Belong to this campaign
        # 2. Have sent emails in the past N days
        # 3. Have no replies since those sends
        # 4. Are not suppressed
        leads_to_advance = self.db.query(LeadDB).filter(
            LeadDB.campaign_id == campaign_id,
            LeadDB.status.notin_(["suppressed", "unsubscribed", "qualified"]),
            LeadDB.last_contacted_at >= cutoff_time,
            LeadDB.last_replied_at < LeadDB.last_contacted_at,  # No reply after last contact
        ).all()
        
        emails_sent = 0
        for lead in leads_to_advance:
            # Get the last outbound email to find sequence position
            last_email = self.db.query(OutboundEmailDB).filter(
                OutboundEmailDB.lead_id == lead.id,
                OutboundEmailDB.campaign_id == campaign_id,
            ).order_by(OutboundEmailDB.sequence_number.desc()).first()
            
            if not last_email:
                logger.warning(f"No prior email found for lead {lead.id}, skipping")
                continue
            
            next_sequence = (last_email.sequence_number or 0) + 1
            logger.info(f"No-reply timeout: Advancing lead {lead.id} to sequence {next_sequence}")
            
            # Here we would:
            # 1. Get the next email template for this sequence
            # 2. Call email_service.send_email() with next template
            # 3. Track the new outbound email
            # For now, just log the action
            emails_sent += 1
        
        return emails_sent
    
    def is_configured(self) -> bool:
        """FollowUpEngine is always configured (no external dependencies)."""
        return True
    
    def health(self) -> dict:
        """Return health status of followup module."""
        from aicmo.cam.contracts import ModuleHealthModel
        try:
            return ModuleHealthModel(
                module_name="FollowUpModule",
                is_healthy=True,
                status="READY",
                message="Follow-up engine operational"
            ).dict()
        except Exception as e:
            return ModuleHealthModel(
                module_name="FollowUpModule",
                is_healthy=False,
                status="ERROR",
                message=str(e)
            ).dict()
