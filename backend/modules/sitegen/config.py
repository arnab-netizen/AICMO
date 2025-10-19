from pydantic import BaseModel
import os


class SiteGenSettings(BaseModel):
    MODULE_NAME: str = "sitegen"
    MODULE_TIER: str = os.getenv("MODULE_TIER", "free")  # free|pro
    API_KEY: str | None = os.getenv("SITEGEN_API_KEY")  # set in env/CI
