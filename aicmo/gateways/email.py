"""
Email delivery adapter.

Concrete implementation of EmailSender interface.
Mock implementation for testing - production would integrate with
SendGrid, Mailgun, AWS SES, or similar service.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from ..domain.execution import ExecutionResult, ExecutionStatus
from .interfaces import EmailSender


class EmailAdapter(EmailSender):
    """
    Email delivery adapter.
    
    Mock implementation that simulates email sending.
    Production would integrate with email service provider (SendGrid, SES, etc.).
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_from_email: Optional[str] = None,
        default_from_name: Optional[str] = None,
    ):
        """
        Initialize email adapter with configuration.
        
        Args:
            api_key: Email service provider API key
            default_from_email: Default sender email address
            default_from_name: Default sender display name
        """
        self.api_key = api_key
        self.default_from_email = default_from_email or "noreply@aicmo.ai"
        self.default_from_name = default_from_name or "AICMO"
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Send an email through the provider.
        
        Mock implementation - returns success for testing.
        Production would call email service API.
        """
        if not self.api_key:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                platform="email",
                error_message="Missing email service API key",
                executed_at=datetime.utcnow(),
            )
        
        if not to_email or "@" not in to_email:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                platform="email",
                error_message=f"Invalid recipient email: {to_email}",
                executed_at=datetime.utcnow(),
            )
        
        # Mock successful send
        mock_message_id = f"email_{to_email.split('@')[0]}_{int(datetime.utcnow().timestamp())}"
        
        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            platform="email",
            platform_post_id=mock_message_id,
            executed_at=datetime.utcnow(),
            metadata={
                "to": to_email,
                "from": from_email or self.default_from_email,
                "from_name": from_name or self.default_from_name,
                "subject": subject,
                "custom_metadata": metadata,
            }
        )
    
    async def validate_configuration(self) -> bool:
        """Check if email service is properly configured."""
        # Mock validation - True if API key exists
        return bool(self.api_key)
