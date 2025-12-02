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

    def apply_fallbacks(self, brand_name: str, industry: str) -> "BrandResearchResult":
        """
        Apply deterministic fallbacks for any empty critical fields.

        This ensures reports never break due to missing research data.
        """
        # Fallback for brand summary
        if not self.brand_summary or len(self.brand_summary.strip()) < 10:
            self.brand_summary = f"{brand_name} is a business in the {industry} industry."

        # Fallback for competitors
        if not self.local_competitors:
            self.local_competitors = [
                Competitor(name="Market Leader", summary="Established competitor in the space"),
                Competitor(name="Emerging Player", summary="Growing presence in the market"),
            ]

        # Fallback for pain points
        if not self.audience_pain_points:
            self.audience_pain_points = [
                "Finding reliable service providers",
                "Understanding pricing and value",
                "Accessing quality information",
            ]

        # Fallback for hashtags
        if not self.hashtag_hints:
            # Generate safe hashtags from industry
            industry_words = industry.replace("/", " ").split()
            self.hashtag_hints = [
                f"#{word.strip()}"
                for word in industry_words
                if word.strip() and len(word.strip()) > 2
            ][:3]
            if not self.hashtag_hints:
                self.hashtag_hints = ["#Business", "#Local", "#Quality"]

        return self
