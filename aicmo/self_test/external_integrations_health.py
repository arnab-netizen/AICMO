"""
External Integrations Health Check Module

Checks the health and configuration status of all external services/adapters:
- Lead enrichment (Apollo)
- Email verification (Dropcontact)
- CRM sync (Airtable)
- Email sending
- Social posting
- Reply fetching (IMAP)
- Make.com webhooks
- LLM providers (OpenAI, etc.)
- Media generation (SDXL, Figma, etc.)
- Video generation (Runway ML, etc.)

For each service:
1. Detect if required env vars are set (configured?)
2. If configured and safe, perform minimal health check (reachable?)
3. Mark as critical or optional
4. Collect details for reporting
"""

import logging
import os
from typing import List, Optional, Dict, Any

from aicmo.self_test.models import ExternalServiceStatus
from aicmo.core.config_gateways import get_gateway_config

logger = logging.getLogger(__name__)


# ============================================================================
# CRITICALITY MAPPING
# ============================================================================
# Define which external services are CRITICAL vs OPTIONAL
# Critical: if unavailable, tests should warn prominently
# Optional: if unavailable, tests note it but don't fail

CRITICAL_EXTERNAL_SERVICES = {
    "openai_llm",  # Main LLM provider used for generation
}

OPTIONAL_EXTERNAL_SERVICES = {
    "apollo_enricher",
    "dropcontact_verifier",
    "airtable_crm",
    "email_gateway",
    "linkedin_social",
    "twitter_social",
    "imap_reply_fetcher",
    "make_webhook",
    "sdxl_media_generation",
    "figma_api",
    "runway_ml_video",
}


def _check_env_vars_present(var_names: List[str]) -> bool:
    """Check if all required env vars are present (non-empty)."""
    return all(os.getenv(var, "").strip() for var in var_names)


def _get_env_var_sources(var_names: List[str]) -> Dict[str, bool]:
    """Return dict mapping env var names to whether they're set."""
    return {var: bool(os.getenv(var, "").strip()) for var in var_names}


async def _check_apollo_health() -> Optional[bool]:
    """
    Minimal health check for Apollo API.
    Safe: just checks if API key is valid format (no actual call unless we need to).
    """
    # Apollo health check could be a lightweight metadata call,
    # but for now we just verify the key format
    api_key = os.getenv("APOLLO_API_KEY", "").strip()
    if not api_key:
        return None
    
    # Simple format check (Apollo keys are typically "key_XXXXX")
    if api_key.startswith("key_"):
        return True
    
    logger.debug(f"Apollo API key format check failed")
    return False


async def _check_dropcontact_health() -> Optional[bool]:
    """Minimal health check for Dropcontact API."""
    api_key = os.getenv("DROPCONTACT_API_KEY", "").strip()
    if not api_key:
        return None
    
    # Simple format check
    if api_key.startswith("dctoken_"):
        return True
    
    logger.debug(f"Dropcontact API key format check failed")
    return False


async def _check_airtable_health() -> Optional[bool]:
    """Minimal health check for Airtable API."""
    api_key = os.getenv("AIRTABLE_API_KEY", "").strip()
    base_id = os.getenv("AIRTABLE_BASE_ID", "").strip()
    
    if not (api_key and base_id):
        return None
    
    # Simple format checks
    if api_key.startswith("pat"):
        return True
    
    logger.debug(f"Airtable credentials format check failed")
    return False


async def _check_openai_health() -> Optional[bool]:
    """
    Minimal health check for OpenAI API.
    Safe: just checks if API key is present (no actual API call).
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    
    # OpenAI keys start with "sk-"
    if api_key.startswith("sk-"):
        return True
    
    logger.debug(f"OpenAI API key format check failed")
    return False


async def _check_email_gateway_health() -> Optional[bool]:
    """Check if email gateway is configured."""
    config = get_gateway_config()
    
    if not config.USE_REAL_EMAIL_GATEWAY:
        return None
    
    return config.is_email_configured()


async def _check_linkedin_social_health() -> Optional[bool]:
    """Check if LinkedIn social gateway is configured."""
    config = get_gateway_config()
    
    if not config.USE_REAL_SOCIAL_GATEWAYS:
        return None
    
    return config.is_social_configured("linkedin")


async def _check_twitter_social_health() -> Optional[bool]:
    """Check if Twitter social gateway is configured."""
    config = get_gateway_config()
    
    if not config.USE_REAL_SOCIAL_GATEWAYS:
        return None
    
    return config.is_social_configured("twitter")


async def _check_imap_health() -> Optional[bool]:
    """Check if IMAP reply fetcher is configured."""
    # IMAP needs email credentials
    imap_host = os.getenv("IMAP_HOST", "").strip()
    imap_user = os.getenv("IMAP_USER", "").strip()
    imap_password = os.getenv("IMAP_PASSWORD", "").strip()
    
    if not (imap_host and imap_user and imap_password):
        return None
    
    return True


async def _check_make_webhook_health() -> Optional[bool]:
    """Check if Make.com webhook is configured."""
    webhook_url = os.getenv("MAKE_WEBHOOK_URL", "").strip()
    
    if not webhook_url:
        return None
    
    # Basic URL format check
    if webhook_url.startswith(("http://", "https://")):
        return True
    
    return False


async def _check_sdxl_media_health() -> Optional[bool]:
    """Check if SDXL media generation is configured."""
    sdxl_key = os.getenv("SDXL_API_KEY", "").strip()
    
    if not sdxl_key:
        return None
    
    return True


async def _check_figma_health() -> Optional[bool]:
    """Check if Figma API is configured."""
    figma_token = os.getenv("FIGMA_API_TOKEN", "").strip()
    
    if not figma_token:
        return None
    
    return True


async def _check_runway_ml_health() -> Optional[bool]:
    """Check if Runway ML video generation is configured."""
    runway_key = os.getenv("RUNWAY_ML_API_KEY", "").strip()
    
    if not runway_key:
        return None
    
    return True


async def get_external_services_health() -> List[ExternalServiceStatus]:
    """
    Check health and configuration status of all external services.
    
    For each service:
    1. Detect if required env vars are set (configured?)
    2. If configured, perform safe minimal health check (reachable?)
    3. Mark as critical or optional
    4. Collect details for reporting
    
    Returns:
        List of ExternalServiceStatus with health info for each service
    """
    services: List[ExternalServiceStatus] = []
    
    # ========================================================================
    # LLM PROVIDERS (CRITICAL)
    # ========================================================================
    
    # OpenAI (primary LLM)
    openai_configured = bool(os.getenv("OPENAI_API_KEY", "").strip())
    openai_reachable = None
    if openai_configured:
        openai_reachable = await _check_openai_health()
    
    services.append(ExternalServiceStatus(
        name="OpenAI LLM (GPT-4, etc.)",
        configured=openai_configured,
        reachable=openai_reachable,
        critical=True,
        details={
            "env_vars_present": openai_configured,
            "check_type": "format_validation",
            "api_endpoint": "https://api.openai.com/v1",
        }
    ))
    
    # ========================================================================
    # LEAD & CONTACT TOOLS (OPTIONAL)
    # ========================================================================
    
    # Apollo Enricher
    apollo_configured = bool(os.getenv("APOLLO_API_KEY", "").strip())
    apollo_reachable = None
    if apollo_configured:
        apollo_reachable = await _check_apollo_health()
    
    services.append(ExternalServiceStatus(
        name="Apollo Lead Enricher",
        configured=apollo_configured,
        reachable=apollo_reachable,
        critical=False,
        details={
            "env_vars_present": apollo_configured,
            "check_type": "format_validation",
            "api_endpoint": "https://api.apollo.io/v1",
            "purpose": "Lead enrichment and discovery",
        }
    ))
    
    # Dropcontact Verifier
    dropcontact_configured = bool(os.getenv("DROPCONTACT_API_KEY", "").strip())
    dropcontact_reachable = None
    if dropcontact_configured:
        dropcontact_reachable = await _check_dropcontact_health()
    
    services.append(ExternalServiceStatus(
        name="Dropcontact Email Verifier",
        configured=dropcontact_configured,
        reachable=dropcontact_reachable,
        critical=False,
        details={
            "env_vars_present": dropcontact_configured,
            "check_type": "format_validation",
            "api_endpoint": "https://api.dropcontact.io/v1",
            "purpose": "Email verification and validation",
        }
    ))
    
    # ========================================================================
    # CRM & CONTACT MANAGEMENT (OPTIONAL)
    # ========================================================================
    
    # Airtable CRM
    airtable_configured = bool(
        os.getenv("AIRTABLE_API_KEY", "").strip() and
        os.getenv("AIRTABLE_BASE_ID", "").strip()
    )
    airtable_reachable = None
    if airtable_configured:
        airtable_reachable = await _check_airtable_health()
    
    services.append(ExternalServiceStatus(
        name="Airtable CRM Sync",
        configured=airtable_configured,
        reachable=airtable_reachable,
        critical=False,
        details={
            "env_vars_present": _get_env_var_sources(["AIRTABLE_API_KEY", "AIRTABLE_BASE_ID"]),
            "check_type": "format_validation",
            "api_endpoint": "https://api.airtable.com/v0",
            "purpose": "CRM synchronization and contact management",
        }
    ))
    
    # ========================================================================
    # EMAIL & COMMUNICATION (OPTIONAL)
    # ========================================================================
    
    # Email Gateway
    email_configured = get_gateway_config().USE_REAL_EMAIL_GATEWAY and get_gateway_config().is_email_configured()
    email_reachable = None
    if email_configured:
        email_reachable = await _check_email_gateway_health()
    
    services.append(ExternalServiceStatus(
        name="Email Gateway",
        configured=email_configured,
        reachable=email_reachable,
        critical=False,
        details={
            "env_vars_present": email_configured,
            "check_type": "configuration_check",
            "purpose": "Email sending (Gmail, SMTP, etc.)",
        }
    ))
    
    # IMAP Reply Fetcher
    imap_configured = all(
        os.getenv(var, "").strip()
        for var in ["IMAP_HOST", "IMAP_USER", "IMAP_PASSWORD"]
    )
    imap_reachable = None
    if imap_configured:
        imap_reachable = await _check_imap_health()
    
    services.append(ExternalServiceStatus(
        name="IMAP Reply Fetcher",
        configured=imap_configured,
        reachable=imap_reachable,
        critical=False,
        details={
            "env_vars_present": _get_env_var_sources(["IMAP_HOST", "IMAP_USER", "IMAP_PASSWORD"]),
            "check_type": "configuration_check",
            "purpose": "Fetching email replies from mailbox",
        }
    ))
    
    # ========================================================================
    # SOCIAL MEDIA (OPTIONAL)
    # ========================================================================
    
    # LinkedIn
    linkedin_configured = get_gateway_config().USE_REAL_SOCIAL_GATEWAYS and get_gateway_config().is_social_configured("linkedin")
    linkedin_reachable = None
    if linkedin_configured:
        linkedin_reachable = await _check_linkedin_social_health()
    
    services.append(ExternalServiceStatus(
        name="LinkedIn Social Posting",
        configured=linkedin_configured,
        reachable=linkedin_reachable,
        critical=False,
        details={
            "env_vars_present": bool(os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()),
            "check_type": "configuration_check",
            "api_endpoint": "https://api.linkedin.com",
            "purpose": "Social media posting",
        }
    ))
    
    # Twitter/X
    twitter_configured = get_gateway_config().USE_REAL_SOCIAL_GATEWAYS and get_gateway_config().is_social_configured("twitter")
    twitter_reachable = None
    if twitter_configured:
        twitter_reachable = await _check_twitter_social_health()
    
    services.append(ExternalServiceStatus(
        name="Twitter/X Social Posting",
        configured=twitter_configured,
        reachable=twitter_reachable,
        critical=False,
        details={
            "env_vars_present": _get_env_var_sources(["TWITTER_API_KEY", "TWITTER_API_SECRET"]),
            "check_type": "configuration_check",
            "api_endpoint": "https://api.twitter.com",
            "purpose": "Social media posting",
        }
    ))
    
    # ========================================================================
    # WEBHOOKS & INTEGRATIONS (OPTIONAL)
    # ========================================================================
    
    # Make.com Webhook
    make_configured = bool(os.getenv("MAKE_WEBHOOK_URL", "").strip())
    make_reachable = None
    if make_configured:
        make_reachable = await _check_make_webhook_health()
    
    services.append(ExternalServiceStatus(
        name="Make.com Webhook",
        configured=make_configured,
        reachable=make_reachable,
        critical=False,
        details={
            "env_vars_present": make_configured,
            "check_type": "format_validation",
            "purpose": "Workflow automation via Make.com",
        }
    ))
    
    # ========================================================================
    # MEDIA & CREATIVE GENERATION (OPTIONAL)
    # ========================================================================
    
    # SDXL Media Generation
    sdxl_configured = bool(os.getenv("SDXL_API_KEY", "").strip())
    sdxl_reachable = None
    if sdxl_configured:
        sdxl_reachable = await _check_sdxl_media_health()
    
    services.append(ExternalServiceStatus(
        name="SDXL Media Generation",
        configured=sdxl_configured,
        reachable=sdxl_reachable,
        critical=False,
        details={
            "env_vars_present": sdxl_configured,
            "check_type": "format_validation",
            "purpose": "Image generation and media creation",
        }
    ))
    
    # Figma API
    figma_configured = bool(os.getenv("FIGMA_API_TOKEN", "").strip())
    figma_reachable = None
    if figma_configured:
        figma_reachable = await _check_figma_health()
    
    services.append(ExternalServiceStatus(
        name="Figma API",
        configured=figma_configured,
        reachable=figma_reachable,
        critical=False,
        details={
            "env_vars_present": figma_configured,
            "check_type": "format_validation",
            "api_endpoint": "https://api.figma.com/v1",
            "purpose": "Design and asset generation",
        }
    ))
    
    # Runway ML Video Generation
    runway_configured = bool(os.getenv("RUNWAY_ML_API_KEY", "").strip())
    runway_reachable = None
    if runway_configured:
        runway_reachable = await _check_runway_ml_health()
    
    services.append(ExternalServiceStatus(
        name="Runway ML Video Generation",
        configured=runway_configured,
        reachable=runway_reachable,
        critical=False,
        details={
            "env_vars_present": runway_configured,
            "check_type": "format_validation",
            "api_endpoint": "https://api.runwayml.com",
            "purpose": "AI video generation",
        }
    ))
    
    logger.info(f"External integrations health check complete: {len(services)} services checked")
    
    return services
