"""
AICMO shared configuration settings.

Phase 4 Lane B: Persistence mode configuration for dual-mode support.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class AicmoSettings(BaseSettings):
    """
    AICMO-wide configuration settings.
    
    Supports environment variable configuration with AICMO_ prefix.
    All settings can be overridden via environment variables.
    """
    
    model_config = ConfigDict(env_prefix="AICMO_")
    
    # Persistence mode: "inmemory" (default) or "db" (real database)
    PERSISTENCE_MODE: str = "inmemory"
    
    # Database connection (only used when PERSISTENCE_MODE=db)
    DATABASE_URL: str = "sqlite:///./aicmo.db"  # Default to SQLite file
    
    # Database connection pool settings (optional, for production)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30  # seconds
    
    # Test mode detection
    TESTING: bool = False  # Set to True in test fixtures


# Singleton settings instance
settings = AicmoSettings()


def is_db_mode() -> bool:
    """Check if persistence mode is database (vs in-memory)."""
    return settings.PERSISTENCE_MODE.lower() == "db"


def is_inmemory_mode() -> bool:
    """Check if persistence mode is in-memory (vs database)."""
    return settings.PERSISTENCE_MODE.lower() == "inmemory"


def is_test_mode() -> bool:
    """Check if running in test mode."""
    return settings.TESTING
