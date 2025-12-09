"""
Gateway factory for creating appropriate adapters based on configuration.

Provides centralized creation of gateway instances with proper fallback logic:
- If real gateway is enabled AND configured: use real adapter
- Otherwise: use safe no-op adapter

Never raises exceptions at import or creation time.

Phase CAM-2: Added factory functions for CAM port adapters (LeadSource, Enricher, Verifier).
"""

import logging
from typing import Optional

from .interfaces import SocialPoster, EmailSender
from .adapters.noop import NoOpEmailSender, NoOpSocialPoster, NoOpCRMSyncer
from ..core.config_gateways import get_gateway_config

# Phase CAM-2: CAM port factories
from .adapters.cam_noop import NoOpLeadSource, NoOpLeadEnricher, NoOpEmailVerifier
from .adapters.apollo_enricher import ApolloEnricher
from .adapters.dropcontact_verifier import DropcontactVerifier
from .adapters.make_webhook import MakeWebhookAdapter

# Phase 8: Reply fetcher factory
from .adapters.reply_fetcher import IMAPReplyFetcher, NoOpReplyFetcher

logger = logging.getLogger(__name__)


def get_email_sender() -> EmailSender:
    """
    Get email sender adapter (real or no-op based on config).
    
    Returns:
        EmailSender instance (real if configured, no-op otherwise)
    """
    config = get_gateway_config()
    
    if config.USE_REAL_EMAIL_GATEWAY and config.is_email_configured():
        try:
            # Try to import and create real email adapter
            from ..email import EmailAdapter
            logger.info("Using real email gateway")
            return EmailAdapter()
        except Exception as e:
            logger.warning(
                f"Failed to create real email gateway: {e}. "
                f"Falling back to no-op mode."
            )
            return NoOpEmailSender()
    else:
        logger.info("Using no-op email gateway (real gateway not enabled or configured)")
        return NoOpEmailSender()


def get_social_poster(platform: str) -> SocialPoster:
    """
    Get social media poster adapter for specific platform.
    
    Args:
        platform: Platform name ('linkedin', 'instagram', 'twitter', etc.)
    
    Returns:
        SocialPoster instance (real if configured, no-op otherwise)
    """
    config = get_gateway_config()
    platform_lower = platform.lower()
    
    if config.USE_REAL_SOCIAL_GATEWAYS and config.is_social_configured(platform_lower):
        try:
            # Try to import and create real social adapter
            if platform_lower == "linkedin":
                from ..social import LinkedInPoster
                logger.info(f"Using real LinkedIn gateway")
                return LinkedInPoster()
            elif platform_lower in ("twitter", "x"):
                from ..social import TwitterPoster
                logger.info(f"Using real Twitter gateway")
                return TwitterPoster()
            elif platform_lower == "instagram":
                from ..social import InstagramPoster
                logger.info(f"Using real Instagram gateway")
                return InstagramPoster()
            else:
                logger.warning(f"Unknown platform '{platform}', using no-op")
                return NoOpSocialPoster(platform_lower)
        except Exception as e:
            logger.warning(
                f"Failed to create real {platform} gateway: {e}. "
                f"Falling back to no-op mode."
            )
            return NoOpSocialPoster(platform_lower)
    else:
        logger.info(f"Using no-op social gateway for {platform} (real gateway not enabled or configured)")
        return NoOpSocialPoster(platform_lower)


def get_crm_syncer() -> NoOpCRMSyncer:
    """
    Get CRM syncer adapter (real or no-op based on config).
    
    Returns:
        CRM syncer instance (real if configured, no-op otherwise)
    """
    config = get_gateway_config()
    
    if config.USE_REAL_CRM_GATEWAY and config.is_crm_configured():
        try:
            # Try to import and create real CRM adapter
            # For now, only Airtable is supported as a simple CRM
            logger.info("Using real CRM gateway (Airtable)")
            # TODO: Import real AirtableCRMSyncer when implemented
            # from ..adapters.airtable import AirtableCRMSyncer
            # return AirtableCRMSyncer()
            logger.warning("Real CRM adapter not yet implemented, using no-op")
            return NoOpCRMSyncer()
        except Exception as e:
            logger.warning(
                f"Failed to create real CRM gateway: {e}. "
                f"Falling back to no-op mode."
            )
            return NoOpCRMSyncer()
    else:
        logger.info("Using no-op CRM gateway (real gateway not enabled or configured)")
        return NoOpCRMSyncer()


# Convenience function for backward compatibility with existing execution service
def get_gateway_for_platform(platform: str):
    """
    Get appropriate gateway adapter for a platform.
    
    Supports both social platforms and email.
    
    Args:
        platform: Platform name ('email', 'linkedin', 'instagram', etc.)
    
    Returns:
        Appropriate gateway adapter
    """
    platform_lower = platform.lower()
    
    if platform_lower == "email":
        return get_email_sender()
    else:
        return get_social_poster(platform_lower)


# ═══════════════════════════════════════════════════════════════════════
# PHASE CAM-2: CAM PORT FACTORIES
# ═══════════════════════════════════════════════════════════════════════


def get_lead_source():
    """
    Get lead source adapter (Apollo, CSV, LinkedIn, etc.).
    
    Returns:
        LeadSourcePort instance (real if configured, no-op otherwise)
    """
    try:
        apollo = ApolloEnricher()  # Note: Apollo handles both discovery and enrichment
        if apollo.is_configured():
            logger.info("Using Apollo as lead source")
            # TODO: Create ApolloLeadSource adapter when needed
            # For now, Apollo enricher is available if needed
    except Exception as e:
        logger.debug(f"Apollo not available: {e}")
    
    logger.debug("Using no-op lead source")
    return NoOpLeadSource()


def get_lead_enricher():
    """
    Get lead enricher adapter (Apollo, Clearbit, Dropcontact, etc.).
    
    Returns:
        LeadEnricherPort instance (real if configured, no-op otherwise)
    """
    try:
        apollo = ApolloEnricher()
        if apollo.is_configured():
            logger.info("Using Apollo enricher")
            return apollo
    except Exception as e:
        logger.debug(f"Apollo enricher not available: {e}")
    
    logger.debug("Using no-op lead enricher")
    return NoOpLeadEnricher()


def get_email_verifier():
    """
    Get email verifier adapter (Dropcontact, NeverBounce, etc.).
    
    Returns:
        EmailVerifierPort instance (real if configured, no-op otherwise)
    """
    try:
        dropcontact = DropcontactVerifier()
        if dropcontact.is_configured():
            logger.info("Using Dropcontact verifier")
            return dropcontact
    except Exception as e:
        logger.debug(f"Dropcontact verifier not available: {e}")
    
    logger.debug("Using no-op email verifier")
    return NoOpEmailVerifier()


def get_make_webhook():
    """
    Get Make.com webhook adapter for event automation.
    
    Returns:
        MakeWebhookAdapter instance (may be unconfigured)
    """
    adapter = MakeWebhookAdapter()
    if adapter.is_configured():
        logger.info("Make.com webhook configured")
    else:
        logger.debug("Make.com webhook not configured")
    return adapter


def get_reply_fetcher():
    """
    Get reply fetcher adapter for inbox integration (Phase 8).
    
    Returns:
        ReplyFetcherPort instance (real IMAP if configured, no-op otherwise)
    """
    try:
        imap = IMAPReplyFetcher()
        if imap.is_configured():
            logger.info("Using IMAP reply fetcher")
            return imap
    except Exception as e:
        logger.debug(f"IMAP reply fetcher not available: {e}")
    
    logger.debug("Using no-op reply fetcher")
    return NoOpReplyFetcher()
