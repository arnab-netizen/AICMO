"""
Outreach Services Base Classes

Provides abstract and utility classes for multi-channel outreach.
Phase B: Email, LinkedIn, Contact Forms outreach coordination.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from aicmo.cam.domain import OutreachMessage, ChannelType, OutreachStatus


@dataclass
class OutreachResult:
    """Result of an outreach attempt."""
    
    success: bool
    channel: ChannelType
    status: OutreachStatus
    message_id: Optional[str] = None
    error: Optional[str] = None
    delivered_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "success": self.success,
            "channel": self.channel.value,
            "status": self.status.value,
            "message_id": self.message_id,
            "error": self.error,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
        }


class OutreachServiceBase(ABC):
    """
    Base class for all outreach services.
    
    Defines the interface that all channel-specific services must implement.
    """
    
    def __init__(self, channel: ChannelType):
        """Initialize service for a channel."""
        self.channel = channel
    
    @abstractmethod
    def send(
        self,
        message: OutreachMessage,
        recipient_email: Optional[str] = None,
        recipient_linkedin_id: Optional[str] = None,
        form_url: Optional[str] = None,
    ) -> OutreachResult:
        """
        Send outreach message via this channel.
        
        Args:
            message: Outreach message to send
            recipient_email: Email address (for email channel)
            recipient_linkedin_id: LinkedIn profile ID (for LinkedIn channel)
            form_url: Contact form URL (for contact form channel)
            
        Returns:
            OutreachResult with success/failure details
        """
        pass
    
    @abstractmethod
    def check_status(self, message_id: str) -> str:
        """
        Check delivery status of a sent message.
        
        Args:
            message_id: ID of the message to check
            
        Returns:
            Status string (SENT, DELIVERED, FAILED, etc.)
        """
        pass
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a message template with personalization.
        
        Args:
            template_name: Name of the template
            context: Personalization variables
            
        Returns:
            Rendered message content
        """
        # Simple placeholder implementation
        # Can be overridden for advanced templating
        content = f"[{template_name}]"
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            content = content.replace(placeholder, str(value))
        return content


class RateLimiter:
    """
    Rate limiting for outreach channels.
    
    Tracks usage per channel, lead, and global limits.
    """
    
    def __init__(self, max_per_day: Optional[int] = None, max_per_hour: Optional[int] = None):
        """Initialize rate limiter with limits."""
        self.max_per_day = max_per_day
        self.max_per_hour = max_per_hour
        self.last_attempt_times = []
    
    def is_rate_limited(self) -> bool:
        """Check if rate limit is exceeded."""
        if not self.max_per_hour and not self.max_per_day:
            return False
        
        now = datetime.utcnow()
        
        # Clean old attempts
        self.last_attempt_times = [
            t for t in self.last_attempt_times
            if (now - t).total_seconds() < 86400  # Keep last 24 hours
        ]
        
        # Check hour limit
        if self.max_per_hour:
            last_hour = [
                t for t in self.last_attempt_times
                if (now - t).total_seconds() < 3600
            ]
            if len(last_hour) >= self.max_per_hour:
                return True
        
        # Check day limit
        if self.max_per_day:
            if len(self.last_attempt_times) >= self.max_per_day:
                return True
        
        return False
    
    def record_attempt(self):
        """Record an outreach attempt."""
        self.last_attempt_times.append(datetime.utcnow())
