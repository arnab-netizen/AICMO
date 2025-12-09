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
