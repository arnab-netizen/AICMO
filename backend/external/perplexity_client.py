from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

import httpx

from backend.core.config import settings
from backend.research_models import BrandResearchResult


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
            print("⚠️ Perplexity API key not configured")
            return None

        # Build the research prompt
        prompt = self._build_research_prompt(brand_name, industry, location)

        # Prepare the request payload
        payload = {
            "model": "sonar",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        # Retry logic with exponential backoff (3 attempts)
        for attempt in range(3):
            try:
                # Make the API call with 20-second timeout
                with httpx.Client(timeout=httpx.Timeout(20.0)) as client:
                    response = client.post(
                        f"{self.base_url}/chat/completions", headers=headers, json=payload
                    )
                    response.raise_for_status()

                # Parse the response
                response_data = response.json()

                # Extract the content from Perplexity's response format
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    content = response_data["choices"][0]["message"]["content"]
                else:
                    print("⚠️ Unexpected Perplexity response format")
                    return None

                # Parse the JSON from the content
                research_data = self._parse_json_content(content)

                if research_data:
                    # Validate and return structured result
                    return BrandResearchResult(**research_data)
                else:
                    print("⚠️ Failed to parse valid JSON from Perplexity response")
                    return None

            except httpx.HTTPStatusError as e:
                print(
                    f"⚠️ Perplexity API HTTP error (attempt {attempt + 1}/3): {e.response.status_code}"
                )
                if attempt < 2:  # Don't sleep on last attempt
                    time.sleep(1 * (attempt + 1))
                continue

            except httpx.RequestError as e:
                print(f"⚠️ Perplexity API request error (attempt {attempt + 1}/3): {str(e)}")
                if attempt < 2:
                    time.sleep(1 * (attempt + 1))
                continue

            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parsing error (attempt {attempt + 1}/3): {str(e)}")
                if attempt < 2:
                    time.sleep(1 * (attempt + 1))
                continue

            except Exception as e:
                print(
                    f"⚠️ Unexpected error during Perplexity research (attempt {attempt + 1}/3): {str(e)}"
                )
                if attempt < 2:
                    time.sleep(1 * (attempt + 1))
                continue

        # All retries exhausted
        print("❌ Perplexity research failed after 3 attempts")
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
  "hashtag_hints": []
}}

Rules:
- Do NOT add commentary, markdown, or explanations.
- Do NOT wrap the JSON in code fences.
- All fields must exist, even if empty.
- Keep answers concise and factual."""

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
