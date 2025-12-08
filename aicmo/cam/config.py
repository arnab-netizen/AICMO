"""
CAM configuration settings.

Phase CAM-5: Configuration for Client Acquisition Mode.
"""

from pydantic_settings import BaseSettings


class CamSettings(BaseSettings):
    """CAM-specific configuration settings."""
    
    CAM_DEFAULT_CAMPAIGN_NAME: str = "AICMO_Prospecting"
    CAM_DEFAULT_CHANNEL: str = "linkedin"
    CAM_DAILY_BATCH_SIZE: int = 25

    class Config:
        env_prefix = "AICMO_"


settings = CamSettings()
