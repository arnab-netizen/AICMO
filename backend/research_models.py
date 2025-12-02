from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, HttpUrl


class Competitor(BaseModel):
    name: str
    summary: Optional[str] = None


class BrandResearchResult(BaseModel):
    """
    Structured result of external brand + location research.

    This is intentionally generic so it can be reused across packs.
    """

    brand_summary: Optional[str] = None
    official_website: Optional[HttpUrl] = None
    main_social_profiles: List[HttpUrl] = []
    current_positioning: Optional[str] = None
    recent_content_themes: List[str] = []
    local_competitors: List[Competitor] = []
    audience_pain_points: List[str] = []
    audience_language_snippets: List[str] = []
    hashtag_hints: List[str] = []
