from __future__ import annotations

import logging
from functools import lru_cache

from typing import Optional

from backend.external.perplexity_client import PerplexityClient
from backend.research_models import BrandResearchResult
from backend.core.config import settings

log = logging.getLogger("brand_research")


@lru_cache(maxsize=256)
def _cached_brand_research(
    brand_name: str,
    industry: str,
    location: str,
) -> Optional[BrandResearchResult]:
    """
    Cached internal helper. Do not call directly; use get_brand_research.
    """
    log.debug(f"[BrandResearch] Cache miss - fetching research for {brand_name}")

    client = PerplexityClient()
    if not client.is_configured():
        log.warning("[BrandResearch] Perplexity client not configured")
        return None

    result = client.research_brand(brand_name=brand_name, industry=industry, location=location)

    if result:
        # Apply fallbacks to ensure data quality
        result = result.apply_fallbacks(brand_name=brand_name, industry=industry)
        log.info(f"[BrandResearch] Successfully fetched and validated research for {brand_name}")
    else:
        log.warning(f"[BrandResearch] Failed to fetch research for {brand_name}")

    return result


def get_brand_research(
    brand_name: str,
    industry: str,
    location: str,
    *,
    enabled: bool | None = None,
) -> Optional[BrandResearchResult]:
    """
    Public entry point for brand research.

    - Respects the AICMO_PERPLEXITY_ENABLED flag.
    - Safely falls back to None if disabled or misconfigured.
    - Uses an in-process cache to avoid repeated external calls.
    """
    if enabled is None:
        enabled = settings.AICMO_PERPLEXITY_ENABLED

    if not enabled:
        log.debug("[BrandResearch] Feature disabled via AICMO_PERPLEXITY_ENABLED=false")
        return None

    if not brand_name or not location:
        log.warning(
            f"[BrandResearch] Missing required fields: brand_name={bool(brand_name)} location={bool(location)}"
        )
        return None

    # Check cache status
    cache_info = _cached_brand_research.cache_info()
    log.debug(
        f"[BrandResearch] Cache stats: hits={cache_info.hits} misses={cache_info.misses} size={cache_info.currsize}"
    )

    result = _cached_brand_research(
        brand_name=brand_name.strip(), industry=industry.strip(), location=location.strip()
    )

    if result:
        log.info(
            f"[BrandResearch] Returning research for {brand_name} (cached={cache_info.hits > 0})"
        )

    return result
