"""
Email provider factory.

Creates the appropriate email provider based on configuration.
"""

import logging
from typing import Union

from aicmo.cam.config import settings
from aicmo.cam.gateways.email_providers.resend import ResendEmailProvider, NoOpEmailProvider
from aicmo.cam.ports.email_provider import EmailProvider


logger = logging.getLogger(__name__)


def get_email_provider() -> Union[ResendEmailProvider, NoOpEmailProvider]:
    """
    Get the configured email provider.
    
    Logic:
    - If RESEND_API_KEY is set: use ResendEmailProvider (with dry-run and allowlist if configured)
    - Otherwise: use NoOpEmailProvider (safe fallback that logs only)
    
    Returns:
        Configured email provider instance (always ready to call send()).
        Never raises.
    
    Note:
        - All settings come from environment variables (AICMO_* prefix)
        - Respects CAM_EMAIL_DRY_RUN and CAM_EMAIL_ALLOWLIST_REGEX
    """
    if settings.RESEND_API_KEY:
        logger.info("Initializing Resend email provider")
        provider = ResendEmailProvider(
            api_key=settings.RESEND_API_KEY,
            from_email=settings.RESEND_FROM_EMAIL,
            dry_run=settings.CAM_EMAIL_DRY_RUN,
            allowlist_regex=settings.CAM_EMAIL_ALLOWLIST_REGEX or None,
        )
        if provider.is_configured():
            logger.info(f"Resend provider ready (from: {settings.RESEND_FROM_EMAIL})")
            return provider
        else:
            logger.warning("Resend provider not properly configured; falling back to NoOp")
            return NoOpEmailProvider()
    else:
        logger.info("No RESEND_API_KEY configured; using NoOp email provider")
        return NoOpEmailProvider()


def is_email_provider_configured() -> bool:
    """
    Check if email provider is properly configured.
    
    Returns:
        True if Resend API key is set; False if using NoOp fallback.
    """
    return bool(settings.RESEND_API_KEY)
