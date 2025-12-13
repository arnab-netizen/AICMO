"""
CAM Email Provider Port

Phase 1: Abstract interface for sending emails via external providers.

Implementations:
- ResendEmailProvider (real, via RESEND_API_KEY)
- SMTPEmailProvider (real, via SMTP config)
- NoOpEmailProvider (safe fallback, logs only)
- DryRunEmailProvider (logs without calling provider)
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Protocol


class EmailStatus(str, Enum):
    """Status of an outbound email."""
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"
    DROPPED = "dropped"


@dataclass
class SendResult:
    """Result of attempting to send an email."""
    
    success: bool
    """True if successfully sent to provider."""
    
    provider_message_id: Optional[str] = None
    """ID assigned by provider (e.g., Resend message ID)."""
    
    error: Optional[str] = None
    """Error message if failed."""
    
    sent_at: Optional[datetime] = None
    """When the email was sent."""


class EmailProvider(Protocol):
    """
    Abstract protocol for sending emails.
    
    Implementations must be idempotent and safe (no partial sends, clear errors).
    """
    
    def is_configured(self) -> bool:
        """
        Check if properly configured with credentials.
        
        Returns:
            True if ready to send; False if missing config.
            Never raises.
        """
        ...
    
    def get_name(self) -> str:
        """Get provider name for logging (e.g., 'Resend', 'SMTP', 'NoOp')."""
        ...
    
    def send(
        self,
        to_email: str,
        from_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        reply_to: Optional[str] = None,
        message_id_header: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> SendResult:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address.
            from_email: Sender email address.
            subject: Email subject.
            html_body: Email body in HTML.
            text_body: Email body in plain text (optional).
            reply_to: Reply-To header (optional).
            message_id_header: Custom Message-ID header for threading (optional).
            metadata: Tags/metadata for provider tracking (optional).
        
        Returns:
            SendResult with success status and provider message ID if successful.
            Never raises - failures are returned as SendResult with success=False.
        """
        ...
