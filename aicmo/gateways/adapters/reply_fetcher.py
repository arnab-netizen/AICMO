"""
Reply Fetcher Adapters for Phase 8

Implementations:
- NoOpReplyFetcher: Safe fallback, returns empty list
- IMAPReplyFetcher: Simple IMAP-based reply fetching (optional, behind env vars)
"""

import os
import logging
from datetime import datetime
from typing import List

from aicmo.cam.ports.reply_fetcher import ReplyFetcherPort, EmailReply

logger = logging.getLogger(__name__)


class NoOpReplyFetcher:
    """
    Safe no-op reply fetcher.
    
    Always configured (returns True), but always returns empty list.
    Used when real fetcher is not available.
    """
    
    def is_configured(self) -> bool:
        """Always returns True (safe to use)."""
        return True
    
    def get_name(self) -> str:
        """Returns 'NoOp'."""
        return "NoOp"
    
    def fetch_new_replies(self, since: datetime) -> List[EmailReply]:
        """
        Always returns empty list.
        
        Args:
            since: Ignored
            
        Returns:
            Empty list (no-op, no real emails)
        """
        return []


class IMAPReplyFetcher:
    """
    IMAP-based reply fetcher.
    
    Requires environment variables:
    - IMAP_REPLY_HOST: IMAP server (e.g., "imap.gmail.com")
    - IMAP_REPLY_PORT: Port (e.g., "993" for SSL)
    - IMAP_REPLY_USER: Email address
    - IMAP_REPLY_PASSWORD: Password or app password
    - IMAP_REPLY_MAILBOX: Mailbox name (default "INBOX")
    
    If any required var is missing, is_configured() returns False and adapter is skipped.
    """
    
    def __init__(self):
        """Initialize with environment variables."""
        self.host = os.getenv("IMAP_REPLY_HOST")
        self.port = os.getenv("IMAP_REPLY_PORT", "993")
        self.user = os.getenv("IMAP_REPLY_USER")
        self.password = os.getenv("IMAP_REPLY_PASSWORD")
        self.mailbox = os.getenv("IMAP_REPLY_MAILBOX", "INBOX")
    
    def is_configured(self) -> bool:
        """
        Check if all required IMAP config is present.
        
        Returns:
            True if host, user, password are all set; False otherwise.
        """
        return bool(self.host and self.user and self.password)
    
    def get_name(self) -> str:
        """Returns 'IMAP'."""
        return "IMAP"
    
    def fetch_new_replies(self, since: datetime) -> List[EmailReply]:
        """
        Fetch new replies from IMAP mailbox since given time.
        
        Args:
            since: Only return emails received after this timestamp
            
        Returns:
            List of EmailReply objects, or empty list if error
        """
        if not self.is_configured():
            logger.debug("IMAP reply fetcher not configured, skipping")
            return []
        
        try:
            import imaplib
            import email
            from email.utils import parsedate_to_datetime
            
            # Connect to IMAP server
            if self.port == "993":
                mail = imaplib.IMAP4_SSL(self.host, int(self.port))
            else:
                mail = imaplib.IMAP4(self.host, int(self.port))
            
            mail.login(self.user, self.password)
            mail.select(self.mailbox)
            
            # Search for emails received since the given time
            since_str = since.strftime("%d-%b-%Y")
            status, msg_ids = mail.search(None, f"SINCE {since_str}")
            
            if status != "OK":
                logger.warning("IMAP search failed")
                return []
            
            replies: List[EmailReply] = []
            
            # Fetch each message
            for msg_id in msg_ids[0].split():
                try:
                    status, msg_data = mail.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue
                    
                    msg_bytes = msg_data[0][1]
                    msg = email.message_from_bytes(msg_bytes)
                    
                    # Extract headers
                    message_id = msg.get("Message-ID", f"<unknown-{msg_id}>")
                    in_reply_to = msg.get("In-Reply-To")
                    thread_id = msg.get("Thread-Topic") or msg.get("Message-ID")
                    from_email = msg.get("From", "unknown")
                    to_email = msg.get("To", "unknown")
                    subject = msg.get("Subject", "(no subject)")
                    
                    # Parse date
                    date_str = msg.get("Date")
                    try:
                        received_at = parsedate_to_datetime(date_str) if date_str else datetime.utcnow()
                    except (TypeError, ValueError):
                        received_at = datetime.utcnow()
                    
                    # Extract body text
                    body_text = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body_text = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                break
                    else:
                        body_text = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                    
                    reply = EmailReply(
                        message_id=message_id,
                        in_reply_to=in_reply_to,
                        thread_id=thread_id,
                        from_email=from_email,
                        to_email=to_email,
                        subject=subject,
                        body_text=body_text,
                        received_at=received_at,
                    )
                    replies.append(reply)
                
                except Exception as e:
                    logger.warning(f"Failed to parse email {msg_id}: {e}")
                    continue
            
            mail.close()
            mail.logout()
            
            logger.info(f"IMAP fetcher returned {len(replies)} new replies")
            return replies
        
        except Exception as e:
            logger.error(f"IMAP reply fetcher error: {e}")
            return []
