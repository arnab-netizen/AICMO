"""
Gateway adapters for external service integrations.

This module provides abstract interfaces and concrete implementations
for social media posting, email delivery, and CRM synchronization.

Includes factory functions for safe adapter creation with automatic
fallback to no-op modes when real gateways are not configured.
"""

from .interfaces import (
    SocialPoster,
    EmailSender,
)
from .social import (
    InstagramPoster,
    LinkedInPoster,
    TwitterPoster,
)
from .email import EmailAdapter
from .execution import execute_content_item, ExecutionService
from .factory import (
    get_email_sender,
    get_social_poster,
    get_crm_syncer,
    get_gateway_for_platform,
)
from .adapters.noop import (
    NoOpEmailSender,
    NoOpSocialPoster,
    NoOpCRMSyncer,
)

__all__ = [
    # Interfaces
    "SocialPoster",
    "EmailSender",
    # Real adapters
    "InstagramPoster",
    "LinkedInPoster",
    "TwitterPoster",
    "EmailAdapter",
    # No-op adapters
    "NoOpEmailSender",
    "NoOpSocialPoster",
    "NoOpCRMSyncer",
    # Factory functions
    "get_email_sender",
    "get_social_poster",
    "get_crm_syncer",
    "get_gateway_for_platform",
    # Execution
    "execute_content_item",
    "ExecutionService",
]
