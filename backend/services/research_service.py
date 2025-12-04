"""
Centralized Research Service - Perplexity Integration Layer

This module provides a unified interface for all research operations,
consolidating Perplexity API calls and ensuring consistent data handling
across the AICMO platform.

Architecture:
    Client Brief → ResearchService → Perplexity API → Structured Research Data
    
Usage:
    research_service = ResearchService()
    research = research_service.fetch_comprehensive_research(brief)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, List
from dataclasses import dataclass

from backend.external.perplexity_client import PerplexityClient
from backend.research_models import BrandResearchResult, Competitor
from backend.core.config import settings
from aicmo.io.client_reports import ClientInputBrief

log = logging.getLogger("research_service")


@dataclass
class CompetitorResearchResult:
    """Structured competitor intelligence from Perplexity."""

    competitors: List[Competitor]
    market_share_insights: List[str]
    competitive_advantages: List[str]
    competitive_threats: List[str]


@dataclass
class AudienceInsightsResult:
    """Structured audience intelligence from Perplexity."""

    pain_points: List[str]
    desires: List[str]
    language_snippets: List[str]
    common_objections: List[str]
    buying_triggers: List[str]


@dataclass
class MarketTrendsResult:
    """Structured market intelligence from Perplexity."""

    industry_trends: List[str]
    growth_drivers: List[str]
    regulatory_changes: List[str]
    technology_disruptions: List[str]
    market_size_data: Optional[str] = None


@dataclass
class ComprehensiveResearchData:
    """
    Complete research package combining all Perplexity-sourced intelligence.

    This is the single source of truth for research data passed to generators.
    """

    brand_research: Optional[BrandResearchResult] = None
    competitor_research: Optional[CompetitorResearchResult] = None
    audience_insights: Optional[AudienceInsightsResult] = None
    market_trends: Optional[MarketTrendsResult] = None

    def is_empty(self) -> bool:
        """Check if research data is substantially empty."""
        return (
            self.brand_research is None
            and self.competitor_research is None
            and self.audience_insights is None
            and self.market_trends is None
        )

    def has_brand_data(self) -> bool:
        """Check if brand research data exists."""
        return self.brand_research is not None

    def has_competitor_data(self) -> bool:
        """Check if competitor research data exists."""
        return (
            self.competitor_research is not None and len(self.competitor_research.competitors) > 0
        )

    def has_audience_data(self) -> bool:
        """Check if audience insights exist."""
        return self.audience_insights is not None and len(self.audience_insights.pain_points) > 0

    def has_market_data(self) -> bool:
        """Check if market trends data exists."""
        return self.market_trends is not None and len(self.market_trends.industry_trends) > 0


class ResearchService:
    """
    Unified service for all Perplexity-backed research operations.

    Responsibilities:
    - Consolidate all Perplexity API calls
    - Provide structured, validated research data
    - Handle fallbacks and error cases gracefully
    - Cache results to minimize API usage
    - Respect configuration flags (AICMO_PERPLEXITY_ENABLED)

    Design Principles:
    - Always returns structured data (never throws on API failure)
    - Uses existing BrandResearchResult + new domain models
    - Testable via dependency injection
    - Config-driven behavior
    """

    def __init__(self, client: Optional[PerplexityClient] = None):
        """
        Initialize research service.

        Args:
            client: Optional PerplexityClient for testing. If None, creates default client.
        """
        self.client = client or PerplexityClient()
        self.enabled = settings.AICMO_PERPLEXITY_ENABLED

    def is_enabled(self) -> bool:
        """Check if research service is enabled and configured."""
        return self.enabled and self.client.is_configured()

    def fetch_comprehensive_research(
        self,
        brief: ClientInputBrief,
        *,
        include_competitors: bool = True,
        include_audience: bool = True,
        include_market: bool = False,
    ) -> ComprehensiveResearchData:
        """
        Fetch all research data for a brief in one unified call.

        This is the primary entry point for generators needing research data.

        Args:
            brief: Client input brief with brand, audience, goal info
            include_competitors: Fetch competitor intelligence
            include_audience: Fetch audience insights
            include_market: Fetch market trends (expensive, opt-in)

        Returns:
            ComprehensiveResearchData with all available research, or empty if disabled
        """
        if not self.is_enabled():
            log.debug("[ResearchService] Service disabled, returning empty research")
            return ComprehensiveResearchData()

        brand_name = brief.brand.brand_name
        industry = brief.brand.industry or "general business"
        location = brief.brand.location or "United States"

        log.info(
            f"[ResearchService] Fetching comprehensive research for {brand_name} "
            f"(competitors={include_competitors}, audience={include_audience}, market={include_market})"
        )

        # Fetch brand research (includes hashtags)
        brand_research = self._fetch_brand_research(brand_name, industry, location)

        # Fetch additional research modules based on flags
        competitor_research = None
        if include_competitors and brand_research:
            competitor_research = self._fetch_competitor_research(brand_name, industry, location)

        audience_insights = None
        if include_audience:
            audience_insights = self._fetch_audience_insights(brief)

        market_trends = None
        if include_market:
            market_trends = self._fetch_market_trends(industry, location)

        result = ComprehensiveResearchData(
            brand_research=brand_research,
            competitor_research=competitor_research,
            audience_insights=audience_insights,
            market_trends=market_trends,
        )

        log.info(
            f"[ResearchService] Research complete: "
            f"brand={result.has_brand_data()}, "
            f"competitors={result.has_competitor_data()}, "
            f"audience={result.has_audience_data()}, "
            f"market={result.has_market_data()}"
        )

        return result

    def _fetch_brand_research(
        self,
        brand_name: str,
        industry: str,
        location: str,
    ) -> Optional[BrandResearchResult]:
        """
        Fetch core brand research including hashtags.

        Uses existing PerplexityClient.research_brand() + hashtag enrichment.
        """
        try:
            result = self.client.research_brand(brand_name, industry, location)

            if result:
                # Enrich with hashtags if not already present
                if not result.keyword_hashtags:
                    try:
                        hashtag_data = asyncio.run(
                            self.client.fetch_hashtag_research(
                                brand_name=brand_name,
                                industry=industry,
                                audience=f"{industry} customers",
                            )
                        )
                        if hashtag_data:
                            result.keyword_hashtags = hashtag_data.get("keyword_hashtags", [])
                            result.industry_hashtags = hashtag_data.get("industry_hashtags", [])
                            result.campaign_hashtags = hashtag_data.get("campaign_hashtags", [])
                    except Exception as e:
                        log.warning(f"[ResearchService] Hashtag enrichment failed: {e}")

                # Apply fallbacks
                result = result.apply_fallbacks(brand_name, industry)

            return result

        except Exception as e:
            log.error(f"[ResearchService] Brand research failed: {e}")
            return None

    def _fetch_competitor_research(
        self,
        brand_name: str,
        industry: str,
        location: str,
    ) -> Optional[CompetitorResearchResult]:
        """
        Fetch detailed competitor intelligence using Perplexity.

        New feature - provides structured competitor data beyond basic brand research.
        """
        try:
            prompt = f"""Research competitors for {brand_name} in the {industry} industry in {location}.

Provide a JSON response with:
{{
  "competitors": [
    {{"name": "Competitor Name", "summary": "Brief description of what makes them notable"}},
    ...
  ],
  "market_share_insights": ["insight 1", "insight 2", ...],
  "competitive_advantages": ["advantage 1", "advantage 2", ...],
  "competitive_threats": ["threat 1", "threat 2", ...]
}}

Focus on:
- Direct competitors in the same market
- Market positioning and differentiation
- Competitive strengths and weaknesses
- Market share or presence indicators

Return ONLY valid JSON, no markdown or explanations."""

            payload = {
                "model": "sonar",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }

            headers = {
                "Authorization": f"Bearer {self.client.api_key}",
                "Content-Type": "application/json",
            }

            import httpx

            with httpx.Client(timeout=httpx.Timeout(20.0)) as http_client:
                response = http_client.post(
                    f"{self.client.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

                response_data = response.json()
                content = response_data["choices"][0]["message"]["content"]

                # Parse JSON from content
                import json

                data = json.loads(content.strip().strip("```json").strip("```"))

                competitors = [Competitor(**c) for c in data.get("competitors", [])]

                return CompetitorResearchResult(
                    competitors=competitors,
                    market_share_insights=data.get("market_share_insights", []),
                    competitive_advantages=data.get("competitive_advantages", []),
                    competitive_threats=data.get("competitive_threats", []),
                )

        except Exception as e:
            log.warning(f"[ResearchService] Competitor research failed: {e}")
            return None

    def _fetch_audience_insights(self, brief: ClientInputBrief) -> Optional[AudienceInsightsResult]:
        """
        Fetch audience insights using Perplexity.

        New feature - scrapes customer reviews, forums, social to understand audience.
        """
        try:
            brand_name = brief.brand.brand_name
            industry = brief.brand.industry or "general business"
            target_audience = brief.audience.primary_customer or "general customers"

            prompt = f"""Research customer insights for {brand_name} in the {industry} industry, targeting {target_audience}.

Provide a JSON response with:
{{
  "pain_points": ["pain point 1", "pain point 2", ...],
  "desires": ["desire 1", "desire 2", ...],
  "language_snippets": ["quote 1", "quote 2", ...],
  "common_objections": ["objection 1", "objection 2", ...],
  "buying_triggers": ["trigger 1", "trigger 2", ...]
}}

Focus on:
- Real customer pain points from reviews/forums
- What customers want/desire from this category
- Actual language customers use (quotes/phrases)
- Common objections to purchase
- Triggers that drive purchase decisions

Return ONLY valid JSON, no markdown or explanations."""

            payload = {
                "model": "sonar",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }

            headers = {
                "Authorization": f"Bearer {self.client.api_key}",
                "Content-Type": "application/json",
            }

            import httpx

            with httpx.Client(timeout=httpx.Timeout(20.0)) as http_client:
                response = http_client.post(
                    f"{self.client.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

                response_data = response.json()
                content = response_data["choices"][0]["message"]["content"]

                # Parse JSON from content
                import json

                data = json.loads(content.strip().strip("```json").strip("```"))

                return AudienceInsightsResult(
                    pain_points=data.get("pain_points", []),
                    desires=data.get("desires", []),
                    language_snippets=data.get("language_snippets", []),
                    common_objections=data.get("common_objections", []),
                    buying_triggers=data.get("buying_triggers", []),
                )

        except Exception as e:
            log.warning(f"[ResearchService] Audience insights failed: {e}")
            return None

    def _fetch_market_trends(
        self,
        industry: str,
        location: str,
    ) -> Optional[MarketTrendsResult]:
        """
        Fetch market trends and intelligence using Perplexity.

        New feature - provides current market dynamics, trends, growth drivers.
        """
        try:
            prompt = f"""Research current market trends for the {industry} industry in {location}.

Provide a JSON response with:
{{
  "industry_trends": ["trend 1", "trend 2", ...],
  "growth_drivers": ["driver 1", "driver 2", ...],
  "regulatory_changes": ["change 1", "change 2", ...],
  "technology_disruptions": ["disruption 1", "disruption 2", ...],
  "market_size_data": "Brief summary of market size/value if available"
}}

Focus on:
- Current industry trends (last 12 months)
- Key growth drivers
- Recent regulatory/policy changes
- Technology disruptions
- Market size data if available

Return ONLY valid JSON, no markdown or explanations."""

            payload = {
                "model": "sonar",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }

            headers = {
                "Authorization": f"Bearer {self.client.api_key}",
                "Content-Type": "application/json",
            }

            import httpx

            with httpx.Client(timeout=httpx.Timeout(20.0)) as http_client:
                response = http_client.post(
                    f"{self.client.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

                response_data = response.json()
                content = response_data["choices"][0]["message"]["content"]

                # Parse JSON from content
                import json

                data = json.loads(content.strip().strip("```json").strip("```"))

                return MarketTrendsResult(
                    industry_trends=data.get("industry_trends", []),
                    growth_drivers=data.get("growth_drivers", []),
                    regulatory_changes=data.get("regulatory_changes", []),
                    technology_disruptions=data.get("technology_disruptions", []),
                    market_size_data=data.get("market_size_data"),
                )

        except Exception as e:
            log.warning(f"[ResearchService] Market trends failed: {e}")
            return None
