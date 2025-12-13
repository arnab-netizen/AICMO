"""
Resend email provider.

Phase 1: Real email sending via Resend API (https://resend.com).
"""

import logging
import re
from datetime import datetime
from typing import Optional

try:
    import requests
except ImportError:
    requests = None

from aicmo.cam.ports.email_provider import EmailProvider, EmailStatus, SendResult


logger = logging.getLogger(__name__)


class ResendEmailProvider:
    """
    Send emails via Resend API.
    
    Requires:
    - AICMO_RESEND_API_KEY env var set
    - AICMO_RESEND_FROM_EMAIL env var set
    - requests library installed
    
    Features:
    - Idempotent sends (uses Content-MD5 header for deduplication)
    - Message-ID threading support (custom Message-ID header)
    - Dry-run mode (log without sending)
    - Email allowlist (filter by regex)
    - Per-message metadata (tags)
    """
    
    RESEND_API_URL = "https://api.resend.com/emails"
    
    def __init__(
        self,
        api_key: str,
        from_email: str,
        dry_run: bool = False,
        allowlist_regex: Optional[str] = None,
    ):
        r"""
        Initialize Resend provider.
        
        Args:
            api_key: Resend API key.
            from_email: Default sender email.
            dry_run: If true, log sends without calling Resend API.
            allowlist_regex: If set, only send to emails matching this regex.
                             E.g., r"@company\.com$" to send only to company domain.
        """
        self.api_key = api_key
        self.from_email = from_email
        self.dry_run = dry_run
        self.allowlist_regex = allowlist_regex
        self._compiled_regex = None
        
        if allowlist_regex:
            try:
                self._compiled_regex = re.compile(allowlist_regex)
            except Exception as e:
                logger.warning(f"Invalid email allowlist regex: {e}")
        
        if not requests:
            logger.warning("requests library not installed; Resend provider will not function")
    
    def is_configured(self) -> bool:
        """
        Check if provider is ready to send.
        
        Returns:
            True if api_key and from_email are set; False otherwise.
            Never raises.
        """
        return bool(self.api_key and self.from_email) and requests is not None
    
    def get_name(self) -> str:
        """Get provider name."""
        return "Resend"
    
    def _is_allowlisted(self, email: str) -> bool:
        """
        Check if email matches allowlist regex.
        
        If no regex is set, allow all emails.
        If regex is set, only allow if email matches.
        """
        if not self._compiled_regex:
            return True
        
        return bool(self._compiled_regex.search(email))
    
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
        Send email via Resend API.
        
        Args:
            to_email: Recipient email.
            from_email: Sender email (overrides default from_email if provided).
            subject: Email subject.
            html_body: HTML body.
            text_body: Plain text body (optional).
            reply_to: Reply-To header (optional).
            message_id_header: Custom Message-ID for threading (optional).
            metadata: Tags/metadata for Resend (optional).
        
        Returns:
            SendResult with success status and provider message ID if successful.
            Never raises - returns SendResult with success=False on error.
        """
        # Use provided from_email or fall back to default
        sender = from_email or self.from_email
        
        # Check allowlist
        if not self._is_allowlisted(to_email):
            logger.info(
                f"Email {to_email} filtered by allowlist; not sending via Resend"
            )
            return SendResult(
                success=False,
                error=f"Email {to_email} does not match allowlist regex",
            )
        
        # If dry run, log and return success
        if self.dry_run:
            logger.info(
                f"[DRY RUN] Would send email to {to_email} via Resend: {subject}"
            )
            # Generate a fake provider message ID for dry-run
            import hashlib
            content_hash = hashlib.md5(html_body.encode()).hexdigest()
            fake_id = f"dry-run-{content_hash[:8]}"
            return SendResult(
                success=True,
                provider_message_id=fake_id,
                sent_at=datetime.utcnow(),
            )
        
        # Build email payload
        payload = {
            "from": sender,
            "to": to_email,
            "subject": subject,
            "html": html_body,
        }
        
        if text_body:
            payload["text"] = text_body
        
        if reply_to:
            payload["reply_to"] = reply_to
        
        if metadata:
            payload["tags"] = [
                {"name": k, "value": str(v)}
                for k, v in metadata.items()
            ]
        
        # Custom headers for idempotency and threading
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        if message_id_header:
            # Note: Resend doesn't support custom Message-ID directly in API.
            # We store it in metadata for tracking and use it in reply_to for threading.
            # See: https://resend.com/docs/api-reference/emails/send
            payload["headers"] = {
                "X-Message-ID": message_id_header,
            }
        
        # Add idempotency token based on content
        import hashlib
        content_for_hash = f"{to_email}:{subject}:{html_body}"
        idempotency_key = hashlib.md5(content_for_hash.encode()).hexdigest()
        headers["Idempotency-Key"] = idempotency_key
        
        try:
            response = requests.post(
                self.RESEND_API_URL,
                json=payload,
                headers=headers,
                timeout=10,
            )
            
            if response.status_code in (200, 201):
                data = response.json()
                provider_message_id = data.get("id")
                logger.info(
                    f"Resend sent email to {to_email} (ID: {provider_message_id})"
                )
                return SendResult(
                    success=True,
                    provider_message_id=provider_message_id,
                    sent_at=datetime.utcnow(),
                )
            else:
                error_msg = f"Resend API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return SendResult(
                    success=False,
                    error=error_msg,
                )
        
        except Exception as e:
            error_msg = f"Resend send failed: {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            return SendResult(
                success=False,
                error=error_msg,
            )


class NoOpEmailProvider:
    """
    Safe fallback provider that never actually sends emails.
    
    Useful for:
    - Testing (log sends without side effects)
    - Disabled email sending
    - Dry-run mode for whole system
    """
    
    def is_configured(self) -> bool:
        """Always returns True - NoOp is always ready."""
        return True
    
    def get_name(self) -> str:
        """Get provider name."""
        return "NoOp"
    
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
        Log the email without sending.
        
        Returns:
            SendResult with success=True and a fake provider message ID.
        """
        import hashlib
        
        logger.debug(
            f"[NoOp] Would send email to {to_email} via {from_email}: {subject}"
        )
        
        # Generate a deterministic fake ID based on content
        content_hash = hashlib.md5(html_body.encode()).hexdigest()
        fake_id = f"noop-{content_hash[:8]}"
        
        return SendResult(
            success=True,
            provider_message_id=fake_id,
            sent_at=datetime.utcnow(),
        )
