"""
Gateway factory for creating appropriate adapters based on configuration.

Provides centralized creation of gateway instances with proper fallback logic:
- If real gateway is enabled AND configured: use real adapter
- Otherwise: use safe no-op adapter

Never raises exceptions at import or creation time.

Phase CAM-2: Added factory functions for CAM port adapters (LeadSource, Enricher, Verifier).

Phase 0 (Step 4): Integrated ProviderChain for multi-provider support with health monitoring
and automatic fallback. Factory maintains backward compatibility while enabling advanced
provider management via ProviderChain registry.
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
from .adapters.airtable_crm import AirtableCRMSyncer

# Phase 8: Reply fetcher factory
from .adapters.reply_fetcher import IMAPReplyFetcher, NoOpReplyFetcher

# Phase 0 Step 4: ProviderChain integration (optional advanced usage)
from .provider_chain import (
    ProviderChain,
    ProviderWrapper,
    register_provider_chain,
    get_provider_chain,
)

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
            # Try Airtable first (simple REST API)
            airtable = AirtableCRMSyncer()
            if airtable.is_configured():
                logger.info("Using Airtable CRM gateway")
                return airtable
            else:
                logger.debug("Airtable not configured, using no-op CRM gateway")
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


# ═══════════════════════════════════════════════════════════════════════
# PHASE 0 STEP 4: PROVIDER CHAIN INTEGRATION
# ═══════════════════════════════════════════════════════════════════════

def setup_provider_chains(is_dry_run: bool = False) -> None:
    """
    Setup ProviderChain instances for all capabilities with health monitoring.
    
    Creates and registers ProviderChain for each capability, enabling:
    - Health-based provider prioritization
    - Automatic fallback on provider failure
    - Provider performance monitoring
    - Self-healing provider selection
    
    Call this once at application startup to enable advanced provider management.
    
    Args:
        is_dry_run: If True, all providers run in simulation mode (no real calls)
        
    Example:
        # At application startup
        setup_provider_chains(is_dry_run=not config.USE_REAL_GATEWAYS)
        
        # Then use ProviderChain for advanced provider management:
        chain = get_provider_chain("email_sending")
        success, result, provider = await chain.invoke("send_email", ...)
    """
    config = get_gateway_config()
    
    # Email Sending Chain
    try:
        email_providers = []
        if config.USE_REAL_EMAIL_GATEWAY and config.is_email_configured():
            real_email = get_email_sender()
            email_providers.append(
                ProviderWrapper(real_email, "real_email_gateway", is_dry_run)
            )
        
        # Fallback to no-op
        email_providers.append(
            ProviderWrapper(NoOpEmailSender(), "noop_email", is_dry_run)
        )
        
        email_chain = ProviderChain(
            capability_name="email_sending",
            providers=email_providers,
            is_dry_run=is_dry_run,
        )
        register_provider_chain(email_chain)
        logger.info(f"Registered ProviderChain: email_sending ({len(email_providers)} providers)")
    except Exception as e:
        logger.error(f"Failed to setup email_sending ProviderChain: {e}")
    
    # Social Posting Chain (multi-platform)
    for platform in ["linkedin", "twitter", "instagram"]:
        try:
            social_providers = []
            if config.USE_REAL_SOCIAL_GATEWAYS and config.is_social_configured(platform):
                real_social = get_social_poster(platform)
                social_providers.append(
                    ProviderWrapper(real_social, f"real_{platform}", is_dry_run)
                )
            
            # Fallback to no-op
            social_providers.append(
                ProviderWrapper(NoOpSocialPoster(platform), f"noop_{platform}", is_dry_run)
            )
            
            social_chain = ProviderChain(
                capability_name=f"social_posting_{platform}",
                providers=social_providers,
                is_dry_run=is_dry_run,
            )
            register_provider_chain(social_chain)
            logger.info(f"Registered ProviderChain: social_posting_{platform} ({len(social_providers)} providers)")
        except Exception as e:
            logger.error(f"Failed to setup social_posting_{platform} ProviderChain: {e}")
    
    # CRM Sync Chain
    try:
        crm_providers = []
        if config.USE_REAL_CRM_GATEWAY and config.is_crm_configured():
            airtable = AirtableCRMSyncer()
            crm_providers.append(
                ProviderWrapper(airtable, "airtable_crm", is_dry_run)
            )
        
        # Fallback to no-op
        crm_providers.append(
            ProviderWrapper(NoOpCRMSyncer(), "noop_crm", is_dry_run)
        )
        
        crm_chain = ProviderChain(
            capability_name="crm_sync",
            providers=crm_providers,
            is_dry_run=is_dry_run,
        )
        register_provider_chain(crm_chain)
        logger.info(f"Registered ProviderChain: crm_sync ({len(crm_providers)} providers)")
    except Exception as e:
        logger.error(f"Failed to setup crm_sync ProviderChain: {e}")
    
    # Lead Enrichment Chain
    try:
        enricher_providers = []
        apollo = ApolloEnricher()
        if apollo.is_configured():
            enricher_providers.append(
                ProviderWrapper(apollo, "apollo_enricher", is_dry_run)
            )
        
        # Fallback to no-op
        enricher_providers.append(
            ProviderWrapper(NoOpLeadEnricher(), "noop_enricher", is_dry_run)
        )
        
        enricher_chain = ProviderChain(
            capability_name="lead_enrichment",
            providers=enricher_providers,
            is_dry_run=is_dry_run,
        )
        register_provider_chain(enricher_chain)
        logger.info(f"Registered ProviderChain: lead_enrichment ({len(enricher_providers)} providers)")
    except Exception as e:
        logger.error(f"Failed to setup lead_enrichment ProviderChain: {e}")
    
    # Email Verification Chain
    try:
        verifier_providers = []
        dropcontact = DropcontactVerifier()
        if dropcontact.is_configured():
            verifier_providers.append(
                ProviderWrapper(dropcontact, "dropcontact_verifier", is_dry_run)
            )
        
        # Fallback to no-op
        verifier_providers.append(
            ProviderWrapper(NoOpEmailVerifier(), "noop_verifier", is_dry_run)
        )
        
        verifier_chain = ProviderChain(
            capability_name="email_verification",
            providers=verifier_providers,
            is_dry_run=is_dry_run,
        )
        register_provider_chain(verifier_chain)
        logger.info(f"Registered ProviderChain: email_verification ({len(verifier_providers)} providers)")
    except Exception as e:
        logger.error(f"Failed to setup email_verification ProviderChain: {e}")
    
    # Reply Fetching Chain
    try:
        fetcher_providers = []
        imap = IMAPReplyFetcher()
        if imap.is_configured():
            fetcher_providers.append(
                ProviderWrapper(imap, "imap_reply_fetcher", is_dry_run)
            )
        
        # Fallback to no-op
        fetcher_providers.append(
            ProviderWrapper(NoOpReplyFetcher(), "noop_reply_fetcher", is_dry_run)
        )
        
        fetcher_chain = ProviderChain(
            capability_name="reply_fetching",
            providers=fetcher_providers,
            is_dry_run=is_dry_run,
        )
        register_provider_chain(fetcher_chain)
        logger.info(f"Registered ProviderChain: reply_fetching ({len(fetcher_providers)} providers)")
    except Exception as e:
        logger.error(f"Failed to setup reply_fetching ProviderChain: {e}")
    
    logger.info("✓ All ProviderChains registered and ready")


def get_email_sending_chain() -> Optional[ProviderChain]:
    """
    Get ProviderChain for email sending (requires setup_provider_chains() call).
    
    Returns:
        ProviderChain for email_sending capability, or None if not registered
    """
    return get_provider_chain("email_sending")


def get_social_posting_chain(platform: str) -> Optional[ProviderChain]:
    """
    Get ProviderChain for social posting on specific platform.
    
    Args:
        platform: Platform name (linkedin, twitter, instagram)
        
    Returns:
        ProviderChain for social_posting_{platform} capability, or None if not registered
    """
    return get_provider_chain(f"social_posting_{platform}")


def get_crm_sync_chain() -> Optional[ProviderChain]:
    """
    Get ProviderChain for CRM synchronization.
    
    Returns:
        ProviderChain for crm_sync capability, or None if not registered
    """
    return get_provider_chain("crm_sync")


def get_lead_enrichment_chain() -> Optional[ProviderChain]:
    """
    Get ProviderChain for lead enrichment.
    
    Returns:
        ProviderChain for lead_enrichment capability, or None if not registered
    """
    return get_provider_chain("lead_enrichment")


def get_email_verification_chain() -> Optional[ProviderChain]:
    """
    Get ProviderChain for email verification.
    
    Returns:
        ProviderChain for email_verification capability, or None if not registered
    """
    return get_provider_chain("email_verification")


def get_reply_fetching_chain() -> Optional[ProviderChain]:
    """
    Get ProviderChain for reply fetching.
    
    Returns:
        ProviderChain for reply_fetching capability, or None if not registered
    """
    return get_provider_chain("reply_fetching")


# Phase 4.5: Media generation support
def get_media_generator_chain():
    """
    Get MediaGeneratorChain for image generation with automatic provider fallback.
    
    Builds chain of media generation providers (SDXL, OpenAI, Flux, etc.)
    with automatic fallback and health monitoring.
    
    Returns:
        MediaGeneratorChain with ordered providers or None if not registered
    """
    from ..media.generators.provider_chain import MediaGeneratorChain
    from ..media.adapters import (
        SDXLAdapter,
        OpenAIImagesAdapter,
        FluxAdapter,
        ReplicateSDXLAdapter,
        FigmaAPIAdapter,
        CanvaAPIAdapter,
        NoOpMediaAdapter,
    )
    
    config = get_gateway_config()
    
    # Build provider list with priority ordering
    providers = [
        SDXLAdapter(dry_run=config.DRY_RUN_MODE),
        OpenAIImagesAdapter(dry_run=config.DRY_RUN_MODE),
        FluxAdapter(dry_run=config.DRY_RUN_MODE),
        ReplicateSDXLAdapter(dry_run=config.DRY_RUN_MODE),
        FigmaAPIAdapter(
            api_token=config.FIGMA_API_TOKEN if hasattr(config, 'FIGMA_API_TOKEN') else None,
            dry_run=config.DRY_RUN_MODE,
        ),
        CanvaAPIAdapter(dry_run=config.DRY_RUN_MODE),
        NoOpMediaAdapter(),  # Always last - safe fallback
    ]
    
    logger.info(f"Created MediaGeneratorChain with {len(providers)} providers")
    return MediaGeneratorChain(
        providers=providers,
        dry_run=config.DRY_RUN_MODE,
    )


# Phase 7: Video generation support
def get_video_generator_chain():
    """
    Get VideoGeneratorChain for video generation with automatic provider fallback.
    
    Builds chain of video generation providers (Runway ML, Pika Labs, Luma Dream, etc.)
    with automatic fallback and health monitoring.
    
    Returns:
        MediaGeneratorChain with ordered video providers or None if not registered
    """
    from ..media.generators.provider_chain import MediaGeneratorChain
    from ..media.adapters import (
        RunwayMLAdapter,
        PikaLabsAdapter,
        LumaDreamAdapter,
        NoOpVideoAdapter,
    )
    
    config = get_gateway_config()
    
    # Build provider list with priority ordering
    providers = [
        RunwayMLAdapter(
            api_key=config.RUNWAY_ML_API_KEY if hasattr(config, 'RUNWAY_ML_API_KEY') else None,
            dry_run=config.DRY_RUN_MODE,
        ),
        PikaLabsAdapter(
            api_key=config.PIKA_LABS_API_KEY if hasattr(config, 'PIKA_LABS_API_KEY') else None,
            dry_run=config.DRY_RUN_MODE,
        ),
        LumaDreamAdapter(
            api_key=config.LUMA_DREAM_API_KEY if hasattr(config, 'LUMA_DREAM_API_KEY') else None,
            dry_run=config.DRY_RUN_MODE,
        ),
        NoOpVideoAdapter(),  # Always last - safe fallback
    ]
    
    logger.info(f"Created video generation chain with {len(providers)} providers")
    return MediaGeneratorChain(
        providers=providers,
        dry_run=config.DRY_RUN_MODE,
    )

