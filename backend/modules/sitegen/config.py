from pydantic import BaseModel, Field
import os


def _get(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


class SiteGenSettings(BaseModel):
    MODULE_NAME: str = "sitegen"
    MODULE_TIER: str = Field(default_factory=lambda: _get("MODULE_TIER", "free"))
    API_KEY: str | None = Field(default_factory=lambda: _get("SITEGEN_API_KEY"))
    SITEGEN_STORE: str = Field(default_factory=lambda: _get("SITEGEN_STORE", "memory"))  # memory|db
    DATABASE_URL: str | None = Field(default_factory=lambda: _get("DATABASE_URL"))
