"""
CAM configuration settings.

Phase CAM-5: Configuration for Client Acquisition Mode.
Phase 1: Extended for email provider (Resend) and caps.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class CamSettings(BaseSettings):
    """CAM-specific configuration settings."""
    
    model_config = ConfigDict(env_prefix="AICMO_")
    
    # Campaign defaults
    CAM_DEFAULT_CAMPAIGN_NAME: str = "AICMO_Prospecting"
    CAM_DEFAULT_CHANNEL: str = "linkedin"
    CAM_DAILY_BATCH_SIZE: int = 25
    
    # Email provider (Resend)
    RESEND_API_KEY: str = ""  # Leave empty to disable Resend sending
    RESEND_FROM_EMAIL: str = "support@aicmo.example.com"
    
    # Email sending caps and safety
    CAM_EMAIL_DAILY_CAP: int = 500  # Max emails to send per day across all campaigns
    CAM_EMAIL_BATCH_CAP: int = 100  # Max emails per single send job
    CAM_EMAIL_DRY_RUN: bool = False  # If true, log sends but don't actually send
    CAM_EMAIL_ALLOWLIST_REGEX: str = ""  # If set, only send to emails matching regex (e.g. @company.com)
    
    # IMAP inbox polling (Phase 2)
    IMAP_SERVER: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    IMAP_EMAIL: str = ""  # Leave empty to disable IMAP polling
    IMAP_PASSWORD: str = ""  # App password for Gmail, regular password for others
    IMAP_POLL_INTERVAL_MINUTES: int = 15
    
    # Decision loop caps (Phase 4)
    CAM_AUTO_PAUSE_REPLY_RATE_THRESHOLD: float = 0.1  # If reply_rate < 10%, flag campaign
    CAM_AUTO_PAUSE_ENABLE: bool = False  # If true, pause campaigns below threshold
    CAM_AUTO_PAUSE_MIN_SENDS_TO_EVALUATE: int = 50  # Only evaluate if sent >= N emails


settings = CamSettings()
