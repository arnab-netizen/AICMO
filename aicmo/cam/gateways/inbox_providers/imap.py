"""
IMAP inbox provider for fetching email replies.

Phase 2: Polls IMAP mailbox for new emails and returns structured reply objects.
"""

import imaplib
import email
import logging
from datetime import datetime
from typing import List, Optional
from email.header import decode_header
from dataclasses import dataclass

from aicmo.cam.ports.reply_fetcher import ReplyFetcherPort


logger = logging.getLogger(__name__)


@dataclass
class EmailReply:
    """Email reply object from IMAP."""
    message_id: str
    in_reply_to: Optional[str]  # In-Reply-To header
    thread_id: Optional[str]  # Message-ID of original (may be same as in_reply_to)
    from_email: str
    to_email: str
    subject: str
    body_text: str
    received_at: datetime


class IMAPInboxProvider:
    """
    Fetch emails from IMAP mailbox (Gmail, Outlook, etc.).
    
    Implements ReplyFetcherPort to integrate with reply detection pipeline.
    
    Features:
    - Connect to IMAP server (Gmail, Outlook, custom)
    - Fetch new emails since last poll
    - Parse MIME structure to extract text body
    - Extract threading headers (Message-ID, In-Reply-To)
    - Safe: Never raises on network errors
    """
    
    def __init__(
        self,
        imap_server: str = "imap.gmail.com",
        imap_port: int = 993,
        email_account: str = "",
        password: str = "",
        mailbox: str = "INBOX",
    ):
        """
        Initialize IMAP provider.
        
        Args:
            imap_server: IMAP server hostname (e.g., imap.gmail.com)
            imap_port: IMAP port (usually 993 for SSL)
            email_account: Email account to connect to
            password: Password or app password (Gmail requires app password)
            mailbox: Mailbox to monitor (default: INBOX)
        """
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.email_account = email_account
        self.password = password
        self.mailbox = mailbox
        self._connection = None
    
    def is_configured(self) -> bool:
        """
        Check if provider is configured.
        
        Returns:
            True if email_account and password are set; False otherwise.
        """
        return bool(self.email_account and self.password)
    
    def get_name(self) -> str:
        """Get provider name."""
        return "IMAP"
    
    def _connect(self) -> bool:
        """
        Connect to IMAP server.
        
        Returns:
            True if successful; False if connection failed.
            Never raises.
        """
        try:
            self._connection = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self._connection.login(self.email_account, self.password)
            logger.info(f"Connected to IMAP server {self.imap_server}")
            return True
        except Exception as e:
            logger.error(f"IMAP connection failed: {type(e).__name__}: {e}")
            return False
    
    def _disconnect(self):
        """Disconnect from IMAP server."""
        try:
            if self._connection:
                self._connection.close()
                self._connection.logout()
        except Exception as e:
            logger.warning(f"IMAP disconnect error: {e}")
    
    def _decode_header_value(self, value: str) -> str:
        """Safely decode email header (handles RFC 2047 encoding)."""
        try:
            if not value:
                return ""
            
            decoded_parts = decode_header(value)
            result = ""
            
            for part, charset in decoded_parts:
                if isinstance(part, bytes):
                    try:
                        result += part.decode(charset or 'utf-8', errors='replace')
                    except Exception:
                        result += part.decode('utf-8', errors='replace')
                else:
                    result += str(part)
            
            return result.strip()
        except Exception as e:
            logger.warning(f"Header decode error: {e}, returning raw value")
            return str(value)
    
    def _extract_text_body(self, msg) -> str:
        """Extract plain text body from email message."""
        body = ""
        
        try:
            if msg.is_multipart():
                # Look for text/plain part
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        charset = part.get_charset()
                        if payload:
                            try:
                                body = payload.decode(charset or 'utf-8', errors='replace')
                            except Exception:
                                body = payload.decode('utf-8', errors='replace')
                        break
            else:
                # Single part email
                payload = msg.get_payload(decode=True)
                charset = msg.get_charset()
                if payload:
                    try:
                        body = payload.decode(charset or 'utf-8', errors='replace')
                    except Exception:
                        body = payload.decode('utf-8', errors='replace')
        except Exception as e:
            logger.warning(f"Body extraction error: {e}")
        
        return body.strip()
    
    def fetch_new_replies(self, since: datetime) -> List[EmailReply]:
        """
        Fetch new emails from mailbox since given time.
        
        Args:
            since: Only fetch emails received after this datetime
        
        Returns:
            List of EmailReply objects (empty list on error)
            Never raises.
        """
        if not self.is_configured():
            logger.warning("IMAP provider not configured (missing email_account or password)")
            return []
        
        # Connect to server
        if not self._connect():
            return []
        
        try:
            # Select mailbox
            status, mailbox_data = self._connection.select(self.mailbox, readonly=True)
            if status != "OK":
                logger.error(f"Failed to select mailbox {self.mailbox}")
                return []
            
            # Search for emails since given time
            # IMAP SINCE format: "DD-MMM-YYYY" (e.g., "13-Dec-2025")
            since_str = since.strftime("%d-%b-%Y")
            status, message_ids = self._connection.search(None, f"SINCE {since_str}")
            
            if status != "OK" or not message_ids[0]:
                logger.info(f"No emails found since {since_str}")
                return []
            
            # Fetch each email
            replies = []
            msg_ids = message_ids[0].split()
            
            logger.info(f"Fetching {len(msg_ids)} emails since {since_str}")
            
            for msg_id in msg_ids:
                try:
                    status, msg_data = self._connection.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue
                    
                    # Parse email
                    msg_bytes = msg_data[0][1]
                    msg = email.message_from_bytes(msg_bytes)
                    
                    # Extract fields
                    from_email = msg.get("From", "")
                    to_email = msg.get("To", "")
                    subject = msg.get("Subject", "")
                    message_id = msg.get("Message-ID", "").strip("<>")
                    in_reply_to = msg.get("In-Reply-To", "").strip("<>")
                    
                    # Decode headers
                    from_email = self._decode_header_value(from_email)
                    to_email = self._decode_header_value(to_email)
                    subject = self._decode_header_value(subject)
                    
                    # Extract email addresses (remove display name)
                    from_email = self._extract_email_address(from_email)
                    to_email = self._extract_email_address(to_email)
                    
                    # Extract body
                    body_text = self._extract_text_body(msg)
                    
                    # Parse received date
                    received_str = msg.get("Date", "")
                    try:
                        from email.utils import parsedate_to_datetime
                        received_at = parsedate_to_datetime(received_str)
                    except Exception:
                        received_at = datetime.utcnow()
                    
                    # Thread ID is usually same as in_reply_to (or Message-ID if not a reply)
                    thread_id = in_reply_to or message_id
                    
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
                    logger.warning(f"Error parsing email {msg_id}: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(replies)} replies")
            return replies
        
        except Exception as e:
            logger.error(f"IMAP fetch error: {type(e).__name__}: {e}")
            return []
        
        finally:
            self._disconnect()
    
    def _extract_email_address(self, email_str: str) -> str:
        """Extract email address from 'Name <email@domain>' format."""
        try:
            if "<" in email_str and ">" in email_str:
                return email_str[email_str.index("<") + 1 : email_str.index(">")]
            return email_str.strip()
        except Exception:
            return email_str.strip()
    
    def is_configured(self) -> bool:
        """Check if IMAP provider is properly configured."""
        from aicmo.cam.config import settings
        return bool(settings.IMAP_SERVER and settings.IMAP_EMAIL and settings.IMAP_PASSWORD)
    
    def health(self) -> dict:
        """Return health status of inbox module."""
        from aicmo.cam.contracts import ModuleHealthModel
        try:
            configured = self.is_configured()
            return ModuleHealthModel(
                module_name="InboxModule",
                is_healthy=configured,
                status="READY" if configured else "DISABLED",
                message="IMAP provider configured" if configured else "IMAP not configured"
            ).dict()
        except Exception as e:
            return ModuleHealthModel(
                module_name="InboxModule",
                is_healthy=False,
                status="ERROR",
                message=str(e)
            ).dict()
