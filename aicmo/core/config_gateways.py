"""
Gateway configuration management.

Controls which gateways are enabled, credentials, and safety modes.
Defaults to NO-OP/dry-run for safety.
"""

import os
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class GatewayConfig:
    """
    Central configuration for all gateway adapters.
    
    Controls real vs no-op behavior, credentials, and safety modes.
    All defaults favor safety: no-op, dry-run, logging only.
    """
    
    # Global switches
    USE_REAL_GATEWAYS: bool = field(default_factory=lambda: os.getenv("USE_REAL_GATEWAYS", "false").lower() == "true")
    DRY_RUN_MODE: bool = field(default_factory=lambda: os.getenv("DRY_RUN_MODE", "true").lower() == "true")
    
    # Email gateway config
    USE_REAL_EMAIL_GATEWAY: bool = field(default_factory=lambda: os.getenv("USE_REAL_EMAIL_GATEWAY", "false").lower() == "true")
    GMAIL_CREDENTIALS_PATH: Optional[str] = field(default_factory=lambda: os.getenv("GMAIL_CREDENTIALS_PATH"))
    GMAIL_TOKEN_PATH: Optional[str] = field(default_factory=lambda: os.getenv("GMAIL_TOKEN_PATH"))
    SMTP_HOST: Optional[str] = field(default_factory=lambda: os.getenv("SMTP_HOST"))
    SMTP_PORT: Optional[int] = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "587")))
    SMTP_USERNAME: Optional[str] = field(default_factory=lambda: os.getenv("SMTP_USERNAME"))
    SMTP_PASSWORD: Optional[str] = field(default_factory=lambda: os.getenv("SMTP_PASSWORD"))
    SMTP_FROM_EMAIL: Optional[str] = field(default_factory=lambda: os.getenv("SMTP_FROM_EMAIL"))
    
    # Social media gateway config
    USE_REAL_SOCIAL_GATEWAYS: bool = field(default_factory=lambda: os.getenv("USE_REAL_SOCIAL_GATEWAYS", "false").lower() == "true")
    LINKEDIN_ACCESS_TOKEN: Optional[str] = field(default_factory=lambda: os.getenv("LINKEDIN_ACCESS_TOKEN"))
    TWITTER_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("TWITTER_API_KEY"))
    TWITTER_API_SECRET: Optional[str] = field(default_factory=lambda: os.getenv("TWITTER_API_SECRET"))
    TWITTER_ACCESS_TOKEN: Optional[str] = field(default_factory=lambda: os.getenv("TWITTER_ACCESS_TOKEN"))
    TWITTER_ACCESS_SECRET: Optional[str] = field(default_factory=lambda: os.getenv("TWITTER_ACCESS_SECRET"))
    BUFFER_ACCESS_TOKEN: Optional[str] = field(default_factory=lambda: os.getenv("BUFFER_ACCESS_TOKEN"))
    
    # CRM gateway config
    USE_REAL_CRM_GATEWAY: bool = field(default_factory=lambda: os.getenv("USE_REAL_CRM_GATEWAY", "false").lower() == "true")
    AIRTABLE_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("AIRTABLE_API_KEY"))
    AIRTABLE_BASE_ID: Optional[str] = field(default_factory=lambda: os.getenv("AIRTABLE_BASE_ID"))
    AIRTABLE_CONTACTS_TABLE: Optional[str] = field(default_factory=lambda: os.getenv("AIRTABLE_CONTACTS_TABLE", "Contacts"))
    AIRTABLE_INTERACTIONS_TABLE: Optional[str] = field(default_factory=lambda: os.getenv("AIRTABLE_INTERACTIONS_TABLE", "Interactions"))
    
    # Phase 4.5: Media generation config
    FIGMA_API_TOKEN: Optional[str] = field(default_factory=lambda: os.getenv("FIGMA_API_TOKEN"))
    SDXL_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("SDXL_API_KEY"))
    OPENAI_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    REPLICATE_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("REPLICATE_API_KEY"))
    CANVA_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("CANVA_API_KEY"))
    
    # Phase 7: Video generation config
    RUNWAY_ML_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("RUNWAY_ML_API_KEY"))
    PIKA_LABS_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("PIKA_LABS_API_KEY"))
    LUMA_DREAM_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("LUMA_DREAM_API_KEY"))
    
    def is_email_configured(self) -> bool:
        """Check if email gateway has necessary credentials."""
        if not self.USE_REAL_EMAIL_GATEWAY:
            return False
        # Check Gmail OR SMTP
        has_gmail = bool(self.GMAIL_CREDENTIALS_PATH and self.GMAIL_TOKEN_PATH)
        has_smtp = bool(self.SMTP_HOST and self.SMTP_USERNAME and self.SMTP_PASSWORD)
        return has_gmail or has_smtp
    
    def is_social_configured(self, platform: str) -> bool:
        """Check if specific social platform has credentials."""
        if not self.USE_REAL_SOCIAL_GATEWAYS:
            return False
        platform_lower = platform.lower()
        if platform_lower == "linkedin":
            return bool(self.LINKEDIN_ACCESS_TOKEN)
        elif platform_lower in ("twitter", "x"):
            return bool(
                self.TWITTER_API_KEY
                and self.TWITTER_API_SECRET
                and self.TWITTER_ACCESS_TOKEN
                and self.TWITTER_ACCESS_SECRET
            )
        elif platform_lower == "buffer":
            return bool(self.BUFFER_ACCESS_TOKEN)
        return False
    
    def is_crm_configured(self) -> bool:
        """Check if CRM gateway has necessary credentials."""
        if not self.USE_REAL_CRM_GATEWAY:
            return False
        return bool(self.AIRTABLE_API_KEY and self.AIRTABLE_BASE_ID)


# Global config instance
_gateway_config: Optional[GatewayConfig] = None


def get_gateway_config() -> GatewayConfig:
    """
    Get or create the global gateway configuration.
    
    Returns:
        Gateway configuration instance (singleton)
    """
    global _gateway_config
    if _gateway_config is None:
        _gateway_config = GatewayConfig()
    return _gateway_config


def reset_gateway_config() -> None:
    """Reset gateway config (useful for testing)."""
    global _gateway_config
    _gateway_config = None


# Multi-Provider Configuration
# Maps capabilities to their available provider chains (primary + fallbacks)
# Order matters: first provider is primary, others are fallbacks
# Reorder to change fallback priority
MULTI_PROVIDER_CONFIG = {
    "email_sending": {
        "description": "Send emails via SMTP/Gmail",
        "providers": ["real_email", "noop_email"],  # Primary: real, Fallback: noop
    },
    "social_posting": {
        "description": "Post content to social platforms",
        "providers": ["real_social", "noop_social"],  # Primary: real (LinkedIn, Twitter, etc), Fallback: noop
    },
    "crm_sync": {
        "description": "Sync contacts and engagement to CRM",
        "providers": ["airtable_crm", "noop_crm"],  # Primary: Airtable, Fallback: noop
    },
    "lead_enrichment": {
        "description": "Enrich leads with additional data",
        "providers": ["apollo_enricher", "noop_lead_enricher"],  # Primary: Apollo API, Fallback: noop
    },
    "email_verification": {
        "description": "Verify email addresses",
        "providers": ["dropcontact_verifier", "noop_email_verifier"],  # Primary: Dropcontact API, Fallback: noop
    },
    "reply_fetching": {
        "description": "Fetch incoming email replies",
        "providers": ["imap_reply_fetcher", "noop_reply_fetcher"],  # Primary: IMAP, Fallback: noop
    },
    "webhook_dispatch": {
        "description": "Send events to external systems (Make.com, Zapier, etc)",
        "providers": ["make_webhook"],  # Primary: Make.com
    },
    "media_generation": {
        "description": "Generate images from text prompts",
        "providers": ["sdxl", "openai_images", "flux", "replicate_sdxl", "figma_api", "canva_api", "noop_media"],
        "comment": "Primary: SDXL, Fallbacks: OpenAI, Flux, Replicate, Figma, Canva, No-op",
    },
    "video_generation": {
        "description": "Generate videos from text prompts (reels, shorts, etc)",
        "providers": ["runway_ml", "pika_labs", "luma_dream", "noop_video"],
        "comment": "Primary: Runway ML, Fallbacks: Pika Labs, Luma Dream, No-op",
    },
}


def get_provider_chain_config(capability: str):
    """
    Get multi-provider configuration for a capability.
    
    Args:
        capability: Capability name (e.g., "email_sending")
        
    Returns:
        Configuration dict with description and provider list, or None if not found
    """
    return MULTI_PROVIDER_CONFIG.get(capability)


def list_capabilities():
    """Get list of all configured capabilities."""
    return list(MULTI_PROVIDER_CONFIG.keys())
