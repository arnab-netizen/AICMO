"""
Proof-mode email adapter.

No-op sender for testing and proof runs.
Records attempts without actually sending emails.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass

from aicmo.gateways.interfaces import EmailSender
from aicmo.domain.execution import ExecutionResult


@dataclass
class ProofSendResult:
    """Result of proof-mode send."""
    provider_message_id: str
    status: str = "SENT_PROOF"
    error: Optional[str] = None


class ProofEmailSenderAdapter(EmailSender):
    """
    Proof-mode email sender.
    
    Simulates email sending without external API calls.
    Generates deterministic message IDs for testing.
    """
    
    def __init__(self):
        self.sent_count = 0
    
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
        Simulate sending email (no-op).
        
        Returns success with fake provider_message_id.
        """
        self.sent_count += 1
        
        # Generate deterministic message ID
        provider_message_id = f"proof_{self.sent_count}_{to_email.replace('@', '_at_')}"
        
        from aicmo.domain.execution import ExecutionStatus
        from datetime import datetime
        
        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            platform="email",
            platform_post_id=provider_message_id,
            metadata={
                "mode": "proof",
                "to": to_email,
                "subject": subject,
                **(metadata or {}),
            },
            executed_at=datetime.utcnow(),
        )
    
    async def validate_configuration(self) -> bool:
        """Proof mode always valid."""
        return True

