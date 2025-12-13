"""
CAM email sending service.

Phase 1: High-level API for sending personalized emails with tracking.

Features:
- Integrates with configured email provider (Resend, SMTP, etc.)
- Handles personalization via EmailTemplate
- Tracks sends in OutboundEmailDB for reply threading and analytics
- Enforces daily/batch caps to prevent runaway sends
- Idempotent: same email + recipient = no duplicate sends
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from aicmo.cam.config import settings
from aicmo.cam.db_models import OutboundEmailDB, LeadDB, CampaignDB
from aicmo.cam.gateways.email_providers.factory import get_email_provider
from aicmo.cam.engine.lead_nurture import EmailTemplate
from aicmo.cam.ports.email_provider import SendResult


logger = logging.getLogger(__name__)


class EmailSendingService:
    """
    Send emails with full tracking and safety controls.
    
    Usage:
        service = EmailSendingService(db_session)
        result = await service.send_email(
            to_email="prospect@company.com",
            campaign_id=1,
            lead_id=1,
            template=email_template,
            personalization_dict={"first_name": "John", ...},
            sequence_number=1,
        )
    """
    
    def __init__(self, db_session: Session):
        """Initialize service with database session."""
        self.db = db_session
        self.provider = get_email_provider()
        self.logger = logger
    
    def _get_content_hash(self, html_body: str) -> str:
        """
        Compute content hash for idempotency detection.
        
        Same content to same recipient = same hash = no duplicate sends.
        """
        return hashlib.md5(html_body.encode()).hexdigest()
    
    def _check_daily_cap(self) -> bool:
        """
        Check if we've reached the daily email cap.
        
        Returns:
            True if under cap; False if at or above cap.
        """
        if settings.CAM_EMAIL_DAILY_CAP <= 0:
            # No cap
            return True
        
        # Count emails sent today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        count = self.db.query(func.count(OutboundEmailDB.id)).filter(
            and_(
                OutboundEmailDB.sent_at >= today_start,
                OutboundEmailDB.status == "SENT",
            )
        ).scalar()
        
        if count >= settings.CAM_EMAIL_DAILY_CAP:
            self.logger.warning(
                f"Daily email cap reached ({count}/{settings.CAM_EMAIL_DAILY_CAP}); "
                "cannot send more emails today"
            )
            return False
        
        return True
    
    def _check_batch_cap(self, additional_count: int = 1) -> bool:
        """
        Check if batch send count would exceed cap.
        
        Args:
            additional_count: Number of emails about to be sent.
        
        Returns:
            True if under cap; False if would exceed.
        """
        if settings.CAM_EMAIL_BATCH_CAP <= 0:
            # No cap
            return True
        
        if additional_count > settings.CAM_EMAIL_BATCH_CAP:
            self.logger.warning(
                f"Batch size ({additional_count}) exceeds cap "
                f"({settings.CAM_EMAIL_BATCH_CAP}); cannot send"
            )
            return False
        
        return True
    
    def _check_idempotency(
        self,
        to_email: str,
        lead_id: int,
        content_hash: str,
        sequence_number: Optional[int] = None,
    ) -> Optional[OutboundEmailDB]:
        """
        Check if this email was already sent (idempotency).
        
        Returns:
            Existing OutboundEmailDB record if found; None otherwise.
            
        Note:
            We check (lead_id, content_hash, sequence_number) to be safe.
            Same content to same lead in same sequence = duplicate.
        """
        query = self.db.query(OutboundEmailDB).filter(
            and_(
                OutboundEmailDB.lead_id == lead_id,
                OutboundEmailDB.content_hash == content_hash,
            )
        )
        
        if sequence_number is not None:
            query = query.filter(OutboundEmailDB.sequence_number == sequence_number)
        
        existing = query.first()
        if existing:
            self.logger.info(
                f"Email already sent to {to_email} (lead_id={lead_id}, "
                f"hash={content_hash[:8]}, seq={sequence_number}); "
                f"returning existing record (id={existing.id})"
            )
        
        return existing
    
    def send_email(
        self,
        to_email: str,
        campaign_id: int,
        lead_id: int,
        template: EmailTemplate,
        personalization_dict: dict,
        sequence_number: Optional[int] = None,
        campaign_sequence_id: Optional[str] = None,
    ) -> Optional[OutboundEmailDB]:
        """
        Send a personalized email with full tracking.
        
        Args:
            to_email: Recipient email address.
            campaign_id: Campaign database ID.
            lead_id: Lead database ID.
            template: EmailTemplate with subject and body.
            personalization_dict: Variables for template personalization.
            sequence_number: Step in the nurture sequence (optional).
            campaign_sequence_id: Campaign-level sequence ID (optional).
        
        Returns:
            OutboundEmailDB record if successfully sent/already sent;
            None if send failed or caps prevented sending.
            
        Side effects:
            - Creates OutboundEmailDB record (always, even on failure)
            - Calls email provider to send
            - Updates lead's last_contacted_at timestamp
        """
        self.logger.info(
            f"Attempting to send email to {to_email} (campaign_id={campaign_id}, "
            f"lead_id={lead_id}, seq={sequence_number})"
        )
        
        # Render email with personalization
        try:
            html_body = template.render(personalization_dict)
            text_body = None  # For simplicity; could extract plain text variant
        except Exception as e:
            self.logger.error(f"Failed to render email template: {e}")
            return None
        
        subject = template.subject
        content_hash = self._get_content_hash(html_body)
        
        # ─────────────────────────────────────────────────────────────────
        # Idempotency check: if already sent, return existing record
        # ─────────────────────────────────────────────────────────────────
        existing = self._check_idempotency(
            to_email=to_email,
            lead_id=lead_id,
            content_hash=content_hash,
            sequence_number=sequence_number,
        )
        if existing:
            return existing
        
        # ─────────────────────────────────────────────────────────────────
        # Safety caps check
        # ─────────────────────────────────────────────────────────────────
        if not self._check_batch_cap(1):
            self.logger.warning(f"Batch cap check failed; not sending to {to_email}")
            return None
        
        if not self._check_daily_cap():
            self.logger.warning(f"Daily cap reached; not sending to {to_email}")
            return None
        
        # ─────────────────────────────────────────────────────────────────
        # Create database record (QUEUED)
        # ─────────────────────────────────────────────────────────────────
        campaign = self.db.query(CampaignDB).filter_by(id=campaign_id).first()
        campaign_name = campaign.name if campaign else f"campaign_{campaign_id}"
        
        outbound_email = OutboundEmailDB(
            lead_id=lead_id,
            campaign_id=campaign_id,
            to_email=to_email,
            from_email=self.provider.get_name() if hasattr(self.provider, 'from_email') else settings.RESEND_FROM_EMAIL,
            subject=subject,
            content_hash=content_hash,
            provider=self.provider.get_name(),
            sequence_number=sequence_number,
            campaign_sequence_id=campaign_sequence_id,
            status="QUEUED",
            email_metadata={
                "template_type": template.sequence_type,
                "campaign_name": campaign_name,
            },
        )
        self.db.add(outbound_email)
        self.db.flush()  # Get the ID but don't commit yet
        
        # ─────────────────────────────────────────────────────────────────
        # Call email provider
        # ─────────────────────────────────────────────────────────────────
        from_email = settings.RESEND_FROM_EMAIL if hasattr(self.provider, 'from_email') else settings.RESEND_FROM_EMAIL
        
        message_id_header = f"<cam-email-{outbound_email.id}@aicmo.local>"
        send_result: SendResult = self.provider.send(
            to_email=to_email,
            from_email=from_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            message_id_header=message_id_header,
            metadata={
                "campaign": campaign_name,
                "lead_id": str(lead_id),
                "sequence": str(sequence_number) if sequence_number else "unknown",
            },
        )
        
        # ─────────────────────────────────────────────────────────────────
        # Update database record based on send result
        # ─────────────────────────────────────────────────────────────────
        if send_result.success:
            outbound_email.status = "SENT"
            outbound_email.provider_message_id = send_result.provider_message_id
            outbound_email.message_id_header = message_id_header
            outbound_email.sent_at = send_result.sent_at or datetime.utcnow()
            self.logger.info(
                f"Email sent to {to_email} (provider_id={send_result.provider_message_id})"
            )
        else:
            outbound_email.status = "FAILED"
            outbound_email.error_message = send_result.error
            self.logger.warning(
                f"Email send failed for {to_email}: {send_result.error}"
            )
        
        # Update lead's last_contacted_at
        lead = self.db.query(LeadDB).filter_by(id=lead_id).first()
        if lead:
            lead.last_contacted_at = datetime.utcnow()
        
        # Commit all changes
        self.db.commit()
        
        return outbound_email
    
    def is_configured(self) -> bool:
        """Check if email provider is properly configured."""
        from aicmo.cam.gateways.email_providers.factory import is_email_provider_configured
        return is_email_provider_configured()
    
    def health(self) -> dict:
        """Return health status of email module."""
        from aicmo.cam.contracts import ModuleHealthModel
        try:
            configured = self.is_configured()
            return ModuleHealthModel(
                module_name="EmailModule",
                is_healthy=configured,
                status="READY" if configured else "DISABLED",
                message="Email provider configured" if configured else "No email provider configured"
            ).dict()
        except Exception as e:
            return ModuleHealthModel(
                module_name="EmailModule",
                is_healthy=False,
                status="ERROR",
                message=str(e)
            ).dict()