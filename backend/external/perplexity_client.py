from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional

import httpx

from backend.core.config import settings
from backend.research_models import BrandResearchResult

log = logging.getLogger("perplexity")


class PerplexityClient:
    """
    Thin client wrapper for Perplexity API.

    Makes real HTTP calls to Perplexity's sonar model for brand research.
    Includes retry logic, error handling, and structured JSON parsing.
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or settings.PERPLEXITY_API_KEY
        self.base_url = base_url or settings.PERPLEXITY_API_BASE

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def research_brand(
        self,
        brand_name: str,
        industry: str,
        location: str,
    ) -> Optional[BrandResearchResult]:
        """
        Return structured research for a brand in a given location.

        Makes a real HTTP call to Perplexity API using the sonar model.
        Returns None if the API call fails after retries.

        Args:
            brand_name: Name of the brand to research
            industry: Industry/category of the brand
            location: Geographic location of the brand

        Returns:
            BrandResearchResult with structured research data, or None on failure
        """
        if not self.is_configured():
            log.warning("[Perplexity] API key not configured - skipping research")
            return None

        log.info(
            f"[Perplexity] Calling API for brand={brand_name!r} location={location!r} industry={industry!r}"
        )

        # Build the research prompt
        prompt = self._build_research_prompt(brand_name, industry, location)

        # Prepare the request payload
        payload = {
            "model": "sonar",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        # Retry logic with exponential backoff (3 attempts max)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                log.debug(f"[Perplexity] Attempt {attempt + 1}/{max_retries}")

                # Make the API call with 20-second timeout
                with httpx.Client(timeout=httpx.Timeout(20.0)) as client:
                    response = client.post(
                        f"{self.base_url}/chat/completions", headers=headers, json=payload
                    )

                    # Check for rate limiting before raising for status
                    if response.status_code == 429:
                        log.warning(
                            f"[Perplexity] Rate limit hit (429) on attempt {attempt + 1}/{max_retries}"
                        )
                        if attempt < max_retries - 1:
                            backoff = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                            log.info(f"[Perplexity] Waiting {backoff}s before retry...")
                            time.sleep(backoff)
                        continue

                    response.raise_for_status()

                # Parse the response
                response_data = response.json()

                # Extract the content from Perplexity's response format
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    content = response_data["choices"][0]["message"]["content"]
                else:
                    log.warning("[Perplexity] Unexpected response format - missing 'choices' field")
                    return None

                # Parse the JSON from the content
                research_data = self._parse_json_content(content)

                if research_data:
                    # Validate and return structured result
                    result = BrandResearchResult(**research_data)

                    # Validate result quality
                    validation_warnings = self._validate_research_result(result)
                    if validation_warnings:
                        log.warning(
                            f"[Perplexity] Data quality warnings: {', '.join(validation_warnings)}"
                        )

                    log.info(
                        f"[Perplexity] Success - parsed fields: "
                        f"summary={bool(result.brand_summary)}, "
                        f"competitors={len(result.local_competitors)}, "
                        f"pain_points={len(result.audience_pain_points)}, "
                        f"hashtags={len(result.hashtag_hints)}"
                    )
                    return result
                else:
                    log.warning("[Perplexity] Failed to parse valid JSON from response")
                    return None

            except httpx.HTTPStatusError as e:
                log.warning(
                    f"[Perplexity] HTTP error on attempt {attempt + 1}/{max_retries}: "
                    f"{e.response.status_code} - {e.response.text[:200]}"
                )
                if attempt < max_retries - 1:
                    backoff = 1 * (attempt + 1)
                    time.sleep(backoff)
                continue

            except httpx.RequestError as e:
                log.warning(
                    f"[Perplexity] Network error on attempt {attempt + 1}/{max_retries}: {type(e).__name__}"
                )
                if attempt < max_retries - 1:
                    backoff = 1 * (attempt + 1)
                    time.sleep(backoff)
                continue

            except json.JSONDecodeError as e:
                log.warning(
                    f"[Perplexity] JSON parse error on attempt {attempt + 1}/{max_retries}: {str(e)[:100]}"
                )
                if attempt < max_retries - 1:
                    backoff = 1 * (attempt + 1)
                    time.sleep(backoff)
                continue

            except Exception as e:
                log.error(
                    f"[Perplexity] Unexpected error on attempt {attempt + 1}/{max_retries}: "
                    f"{type(e).__name__}: {str(e)[:200]}"
                )
                if attempt < max_retries - 1:
                    backoff = 1 * (attempt + 1)
                    time.sleep(backoff)
                continue

        # All retries exhausted
        log.error(
            f"[Perplexity] Research failed after {max_retries} attempts for brand={brand_name!r}"
        )
        return None

    def _build_research_prompt(self, brand_name: str, industry: str, location: str) -> str:
        """Build the exact prompt for Perplexity API."""
        return f"""You are a research engine for a marketing strategy tool.

Given:
Brand name: {brand_name}
Industry: {industry}
Location: {location}

Search the web and return ONLY valid JSON matching this exact structure:

{{
  "brand_summary": "",
  "official_website": "",
  "main_social_profiles": [],
  "current_positioning": "",
  "recent_content_themes": [],
  "local_competitors": [
    {{"name": "", "summary": ""}},
    {{"name": "", "summary": ""}}
  ],
  "audience_pain_points": [],
  "audience_language_snippets": [],
  "hashtag_hints": [],
  "keyword_hashtags": [],
  "industry_hashtags": [],
  "campaign_hashtags": []
}}

Rules:
- Do NOT add commentary, markdown, or explanations.
- Do NOT wrap the JSON in code fences.
- All fields must exist, even if empty.
- Hashtag fields (keyword_hashtags, industry_hashtags, campaign_hashtags) must be arrays of strings starting with #.
- Keep answers concise and factual."""

    def _validate_research_result(self, result: BrandResearchResult) -> list[str]:
        """
        Validate the quality of research results and return warnings.

        Returns:
            List of warning messages for any quality issues found
        """
        warnings = []

        if not result.brand_summary or len(result.brand_summary.strip()) < 10:
            warnings.append("brand_summary is empty or too short")

        if not result.local_competitors:
            warnings.append("no local_competitors found")

        if not result.audience_pain_points:
            warnings.append("no audience_pain_points found")

        if not result.hashtag_hints:
            warnings.append("no hashtag_hints found")

        return warnings

    def _parse_json_content(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from Perplexity response content.

        Handles cases where the JSON might be wrapped in markdown code fences
        or have extra whitespace/text.
        """
        try:
            # First, try direct parsing
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code fences
        try:
            # Remove code fences if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            # Try parsing again
            return json.loads(content.strip())
        except (json.JSONDecodeError, IndexError):
            pass

        # Try to find JSON object in the content
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass

        # All parsing attempts failed
        return None

    async def fetch_hashtag_research(
        self,
        brand_name: str,
        industry: str,
        audience: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch structured hashtag research from Perplexity API.

        Calls Perplexity Sonar with a system prompt that produces ONLY a JSON dict:
        - keyword_hashtags: 10-20 highly relevant tags
        - industry_hashtags: 10-20 tags based on industry
        - campaign_hashtags: 10 tags suitable for short-term promotions

        Args:
            brand_name: Name of the brand
            industry: Industry/category
            audience: Target audience description

        Returns:
            Dict with keyword_hashtags, industry_hashtags, campaign_hashtags arrays,
            or None on failure
        """
        if not self.is_configured():
            log.warning("[Perplexity] API key not configured - skipping hashtag research")
            return None

        log.info(
            f"[Perplexity] Fetching hashtag research for brand={brand_name!r} industry={industry!r}"
        )

        # Build the hashtag-specific prompt
        prompt = f"""You are a social media hashtag research engine.

Given:
Brand: {brand_name}
Industry: {industry}
Audience: {audience}

Return ONLY valid JSON (no commentary, no markdown, no code fences):

{{
  "keyword_hashtags": ["#hashtag1", "#hashtag2", ...],
  "industry_hashtags": ["#industry1", "#industry2", ...],
  "campaign_hashtags": ["#campaign1", "#campaign2", ...]
}}

Requirements:
- keyword_hashtags: 10-20 highly relevant tags based on brand/product keywords
- industry_hashtags: 10-20 tags commonly used in {industry}
- campaign_hashtags: 10 tags suitable for promotions/launches
- All hashtags MUST start with #
- All hashtags MUST be longer than 3 characters
- No explanations, only JSON"""

        # Prepare the request payload
        payload = {
            "model": "sonar",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        # Retry logic with exponential backoff (3 attempts max)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                log.debug(f"[Perplexity Hashtags] Attempt {attempt + 1}/{max_retries}")

                # Make the API call with 20-second timeout
                with httpx.Client(timeout=httpx.Timeout(20.0)) as client:
                    response = client.post(
                        f"{self.base_url}/chat/completions", headers=headers, json=payload
                    )

                    # Check for rate limiting
                    if response.status_code == 429:
                        log.warning(
                            f"[Perplexity Hashtags] Rate limit hit (429) on attempt {attempt + 1}/{max_retries}"
                        )
                        if attempt < max_retries - 1:
                            backoff = 2**attempt
                            log.info(f"[Perplexity Hashtags] Waiting {backoff}s before retry...")
                            time.sleep(backoff)
                        continue

                    response.raise_for_status()

                # Parse the response
                response_data = response.json()

                # Extract the content
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    content = response_data["choices"][0]["message"]["content"]
                else:
                    log.warning(
                        "[Perplexity Hashtags] Unexpected response format - missing 'choices' field"
                    )
                    return None

                # Parse the JSON from the content
                hashtag_data = self._parse_json_content(content)

                if hashtag_data:
                    # Validate hashtag format
                    validated_data = self._validate_hashtag_data(hashtag_data)
                    if validated_data:
                        log.info(
                            f"[Perplexity Hashtags] Success - "
                            f"keyword={len(validated_data.get('keyword_hashtags', []))}, "
                            f"industry={len(validated_data.get('industry_hashtags', []))}, "
                            f"campaign={len(validated_data.get('campaign_hashtags', []))}"
                        )
                        return validated_data
                    else:
                        log.warning("[Perplexity Hashtags] Validation failed for hashtag data")
                        return None
                else:
                    log.warning("[Perplexity Hashtags] Failed to parse valid JSON from response")
                    return None

            except httpx.HTTPStatusError as e:
                log.warning(
                    f"[Perplexity Hashtags] HTTP error on attempt {attempt + 1}/{max_retries}: "
                    f"{e.response.status_code}"
                )
                if attempt < max_retries - 1:
                    backoff = 1 * (attempt + 1)
                    time.sleep(backoff)
                continue

            except httpx.RequestError as e:
                log.warning(
                    f"[Perplexity Hashtags] Network error on attempt {attempt + 1}/{max_retries}: "
                    f"{type(e).__name__}"
                )
                if attempt < max_retries - 1:
                    backoff = 1 * (attempt + 1)
                    time.sleep(backoff)
                continue

            except json.JSONDecodeError:
                log.warning(
                    f"[Perplexity Hashtags] JSON parse error on attempt {attempt + 1}/{max_retries}"
                )
                if attempt < max_retries - 1:
                    backoff = 1 * (attempt + 1)
                    time.sleep(backoff)
                continue

            except Exception as e:
                log.error(
                    f"[Perplexity Hashtags] Unexpected error on attempt {attempt + 1}/{max_retries}: "
                    f"{type(e).__name__}: {str(e)[:200]}"
                )
                if attempt < max_retries - 1:
                    backoff = 1 * (attempt + 1)
                    time.sleep(backoff)
                continue

        # All retries exhausted
        log.error(
            f"[Perplexity Hashtags] Hashtag research failed after {max_retries} attempts for brand={brand_name!r}"
        )
        return None

    def _validate_hashtag_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validate and clean hashtag data from Perplexity.

        Ensures:
        - All hashtags start with #
        - All hashtags are longer than 3 characters
        - No duplicates within each category

        Returns:
            Cleaned data dict or None if validation fails
        """
        validated = {}

        for field in ["keyword_hashtags", "industry_hashtags", "campaign_hashtags"]:
            if field not in data or not isinstance(data[field], list):
                validated[field] = []
                continue

            clean_tags = []
            seen = set()

            for tag in data[field]:
                if not isinstance(tag, str):
                    continue

                # Ensure starts with #
                if not tag.startswith("#"):
                    tag = f"#{tag}"

                # Validate length (> 3 chars including #)
                if len(tag) < 4:
                    continue

                # Remove duplicates
                tag_lower = tag.lower()
                if tag_lower in seen:
                    continue

                clean_tags.append(tag)
                seen.add(tag_lower)

            validated[field] = clean_tags

        # Ensure we got at least some hashtags
        total_tags = sum(len(validated[f]) for f in validated)
        if total_tags == 0:
            log.warning("[Perplexity Hashtags] Validation failed - no valid hashtags found")
            return None

        return validated
