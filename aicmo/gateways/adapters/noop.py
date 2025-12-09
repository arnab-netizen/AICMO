"""
No-op gateway adapters for safe development and testing.

These adapters implement all gateway interfaces but perform NO real network calls.
They log actions and return success results, making them safe for:
- Development without credentials
- Testing without external dependencies
- Dry-run modes in production
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..interfaces import SocialPoster, EmailSender
from ...domain.execution import ContentItem, ExecutionResult, ExecutionStatus

logger = logging.getLogger(__name__)


class NoOpEmailSender(EmailSender):
    """
    No-op email sender that logs but doesn't send.
    
    Safe default when real email gateway is not configured.
    Useful for development, testing, and dry-run modes.
    """
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """Log email send without actually sending."""
        logger.info(
            f"[NO-OP EMAIL] Would send email:\n"
            f"  To: {to_email}\n"
            f"  From: {from_name or 'AICMO'} <{from_email or 'noreply@aicmo.local'}>\n"
            f"  Subject: {subject}\n"
            f"  Body length: {len(html_body)} chars\n"
            f"  Metadata: {metadata}"
        )
        
        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            platform="email",
            platform_post_id=f"noop-email-{datetime.utcnow().timestamp()}",
            metadata={
                "mode": "no-op",
                "to": to_email,
                "subject": subject,
                "body_length": len(html_body),
                **(metadata or {}),
            },
            executed_at=datetime.utcnow(),
        )
    
    async def validate_configuration(self) -> bool:
        """No-op always returns True (no config needed)."""
        return True


class NoOpSocialPoster(SocialPoster):
    """
    No-op social poster that logs but doesn't post.
    
    Safe default when real social gateways are not configured.
    """
    
    def __init__(self, platform_name: str):
        """
        Initialize no-op poster for a specific platform.
        
        Args:
            platform_name: Platform identifier (e.g., 'linkedin', 'instagram')
        """
        self.platform_name = platform_name.lower()
    
    async def post(self, content: ContentItem) -> ExecutionResult:
        """Log social post without actually posting."""
        logger.info(
            f"[NO-OP {self.platform_name.upper()}] Would post content:\n"
            f"  Platform: {content.platform}\n"
            f"  Title: {content.title}\n"
            f"  Body: {content.body_text[:100]}...\n"
            f"  Hook: {content.hook}\n"
            f"  CTA: {content.cta}"
        )
        
        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            platform=self.platform_name,
            platform_post_id=f"noop-{self.platform_name}-{datetime.utcnow().timestamp()}",
            metadata={
                "mode": "no-op",
                "content_length": len(content.body_text),
                "has_hook": bool(content.hook),
                "has_cta": bool(content.cta),
            },
            executed_at=datetime.utcnow(),
        )
    
    async def validate_credentials(self) -> bool:
        """No-op always returns True (no credentials needed)."""
        return True
    
    def get_platform_name(self) -> str:
        """Return platform name."""
        return self.platform_name


class NoOpCRMSyncer:
    """
    No-op CRM syncer that logs but doesn't sync.
    
    Safe default when real CRM gateway is not configured.
    """
    
    def upsert_contact(self, contact_data: Dict[str, Any]) -> ExecutionResult:
        """Log contact upsert without actually syncing."""
        logger.info(
            f"[NO-OP CRM] Would upsert contact:\n"
            f"  Email: {contact_data.get('email')}\n"
            f"  Name: {contact_data.get('name')}\n"
            f"  Fields: {list(contact_data.keys())}"
        )
        
        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            platform="crm",
            platform_post_id=f"noop-crm-contact-{datetime.utcnow().timestamp()}",
            metadata={
                "mode": "no-op",
                "contact_email": contact_data.get("email"),
                "fields_count": len(contact_data),
            },
            executed_at=datetime.utcnow(),
        )
    
    def log_interaction(self, interaction_data: Dict[str, Any]) -> ExecutionResult:
        """Log interaction without actually syncing."""
        logger.info(
            f"[NO-OP CRM] Would log interaction:\n"
            f"  Contact: {interaction_data.get('contact_email')}\n"
            f"  Type: {interaction_data.get('interaction_type')}\n"
            f"  Details: {interaction_data.get('details')}"
        )
        
        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            platform="crm",
            platform_post_id=f"noop-crm-interaction-{datetime.utcnow().timestamp()}",
            metadata={
                "mode": "no-op",
                "interaction_type": interaction_data.get("interaction_type"),
            },
            executed_at=datetime.utcnow(),
        )
    
    def validate_configuration(self) -> bool:
        """No-op always returns True (no config needed)."""
        return True
