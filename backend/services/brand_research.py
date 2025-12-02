from __future__ import annotations

from functools import lru_cache

from typing import Optional

from backend.external.perplexity_client import PerplexityClient
from backend.research_models import BrandResearchResult
from backend.core.config import settings


@lru_cache(maxsize=256)
def _cached_brand_research(
    brand_name: str,
    industry: str,
    location: str,
) -> Optional[BrandResearchResult]:
    """
    Cached internal helper. Do not call directly; use get_brand_research.
    """
    client = PerplexityClient()
    if not client.is_configured():
        return None

    return client.research_brand(brand_name=brand_name, industry=industry, location=location)


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
        return None

    if not brand_name or not location:
        return None

    return _cached_brand_research(
        brand_name=brand_name.strip(), industry=industry.strip(), location=location.strip()
    )
