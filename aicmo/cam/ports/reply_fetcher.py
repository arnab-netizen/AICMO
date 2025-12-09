"""
CAM Reply Fetcher Port

Phase 8: Abstract interface for fetching email replies from campaign inboxes.

Follows the port/adapter pattern used by LeadSourcePort, LeadEnricherPort, etc.
"""

from datetime import datetime
from typing import List, Protocol
from dataclasses import dataclass


@dataclass
class EmailReply:
    """Raw email reply fetched from inbox."""
    
    message_id: str
    """Unique ID of this email (RFC 2822 Message-ID)"""
    
    in_reply_to: str | None
    """Message-ID of the message being replied to"""
    
    thread_id: str | None
    """Thread/conversation ID (Gmail, etc.)"""
    
    from_email: str
    """Sender's email address"""
    
    to_email: str
    """Recipient email (usually our campaign send address)"""
    
    subject: str
    """Email subject line"""
    
    body_text: str
    """Plain text body"""
    
    received_at: datetime
    """When the reply was received"""


class ReplyFetcherPort(Protocol):
    """
    Abstract port for fetching email replies from campaign inboxes.
    
    Implementations:
    - GmailReplyFetcher (real, behind GMAIL_* env vars)
    - IMAPReplyFetcher (real, behind IMAP_* env vars)
    - NoOpReplyFetcher (safe fallback)
    """
    
    def is_configured(self) -> bool:
        """
        Check if this adapter is properly configured with credentials.
        
        Returns:
            True if ready to fetch; False if missing config/credentials.
            Never raises.
        """
        ...
    
    def get_name(self) -> str:
        """Get adapter name for logging (e.g. 'Gmail', 'IMAP', 'NoOp')."""
        ...
    
    def fetch_new_replies(self, since: datetime) -> List[EmailReply]:
        """
        Fetch all new replies received since the given datetime.
        
        Args:
            since: Only return replies received after this time.
            
        Returns:
            List of EmailReply objects, newest first.
            Empty list if no replies or if unconfigured.
            Never raises - failures are logged and empty list returned.
        """
        ...
