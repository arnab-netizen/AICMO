import os


class Settings:
    """Minimal settings loader using environment variables.

    Avoids pydantic so the code runs in environments with either pydantic v1 or v2
    (and without pydantic-settings installed).
    """
    APP_NAME: str = os.getenv("APP_NAME", "AICMO API")
    DB_URL: str = os.getenv("DB_URL", "postgresql+psycopg://app:app@localhost:5432/appdb")
    DB_CONNECT_TIMEOUT: int = int(os.getenv("DB_CONNECT_TIMEOUT", "2"))
    DB_STARTUP_RETRY_SECS: int = int(os.getenv("DB_STARTUP_RETRY_SECS", "20"))


settings = Settings()
