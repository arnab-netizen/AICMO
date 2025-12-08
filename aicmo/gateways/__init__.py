"""
Gateway adapters for external service integrations.

This module provides abstract interfaces and concrete implementations
for social media posting, email delivery, and CRM synchronization.
"""

from .interfaces import (
    SocialPoster,
    EmailSender,
    CRMSyncer,
)
from .social import (
    InstagramPoster,
    LinkedInPoster,
    TwitterPoster,
)
from .email import EmailAdapter
from .execution import execute_content_item, ExecutionService

__all__ = [
    "SocialPoster",
    "EmailSender",
    "CRMSyncer",
    "InstagramPoster",
    "LinkedInPoster",
    "TwitterPoster",
    "EmailAdapter",
    "execute_content_item",
    "ExecutionService",
]
