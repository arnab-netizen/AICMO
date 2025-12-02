import os
import logging


class Settings:
    """Minimal settings loader using environment variables.

    Avoids pydantic so the code runs in environments with either pydantic v1 or v2
    (and without pydantic-settings installed).
    """

    APP_NAME: str = os.getenv("APP_NAME", "AICMO API")
    DB_URL: str = os.getenv("DB_URL") or os.getenv("DATABASE_URL") or "sqlite+pysqlite:///:memory:"
    DB_CONNECT_TIMEOUT: int = int(os.getenv("DB_CONNECT_TIMEOUT", "2"))
    DB_STARTUP_RETRY_SECS: int = int(os.getenv("DB_STARTUP_RETRY_SECS", "20"))

    # Logging configuration
    LOGGING_LEVEL: str = os.getenv("LOGGING_LEVEL", "INFO").upper()

    # Perplexity research integration
    PERPLEXITY_API_KEY: str | None = os.getenv("PERPLEXITY_API_KEY")
    PERPLEXITY_API_BASE: str = os.getenv("PERPLEXITY_API_BASE", "https://api.perplexity.ai")
    AICMO_PERPLEXITY_ENABLED: bool = os.getenv("AICMO_PERPLEXITY_ENABLED", "").lower() in (
        "true",
        "1",
        "yes",
    )


settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOGGING_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
