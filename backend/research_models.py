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

    # Perplexity-Powered Hashtag Strategy v1
    keyword_hashtags: Optional[List[str]] = None
    industry_hashtags: Optional[List[str]] = None
    campaign_hashtags: Optional[List[str]] = None

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

        # Fallback for keyword_hashtags
        if self.keyword_hashtags is None:
            self.keyword_hashtags = []
        else:
            # Remove duplicates and ensure all start with #
            clean_keywords = []
            seen = set()
            for tag in self.keyword_hashtags:
                if not tag.startswith("#"):
                    tag = f"#{tag}"
                tag_lower = tag.lower()
                if tag_lower not in seen and len(tag) > 1:
                    clean_keywords.append(tag)
                    seen.add(tag_lower)
            self.keyword_hashtags = clean_keywords

        # Fallback for industry_hashtags
        if self.industry_hashtags is None:
            self.industry_hashtags = []
        else:
            # Remove duplicates and ensure all start with #
            clean_industry = []
            seen = set()
            for tag in self.industry_hashtags:
                if not tag.startswith("#"):
                    tag = f"#{tag}"
                tag_lower = tag.lower()
                if tag_lower not in seen and len(tag) > 1:
                    clean_industry.append(tag)
                    seen.add(tag_lower)
            self.industry_hashtags = clean_industry

        # Fallback for campaign_hashtags
        if self.campaign_hashtags is None:
            self.campaign_hashtags = []
        else:
            # Remove duplicates and ensure all start with #
            clean_campaign = []
            seen = set()
            for tag in self.campaign_hashtags:
                if not tag.startswith("#"):
                    tag = f"#{tag}"
                tag_lower = tag.lower()
                if tag_lower not in seen and len(tag) > 1:
                    clean_campaign.append(tag)
                    seen.add(tag_lower)
            self.campaign_hashtags = clean_campaign

        return self
