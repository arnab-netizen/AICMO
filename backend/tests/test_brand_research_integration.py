"""
Tests for brand research integration.

Validates that the Perplexity research layer:
- Respects feature flags
- Returns None when disabled
- Returns structured data when enabled (using stub)
- Integrates cleanly with BrandBrief
"""

from backend.research_models import BrandResearchResult
from backend.services.brand_research import get_brand_research
from backend.core.config import settings


def test_brand_research_disabled_returns_none(monkeypatch):
    """When AICMO_PERPLEXITY_ENABLED=False, research should return None."""
    monkeypatch.setattr(settings, "AICMO_PERPLEXITY_ENABLED", False, raising=False)
    result = get_brand_research("Demo Brand", "Coffeehouse", "Kolkata, India")
    assert result is None


def test_brand_research_enabled_stub(monkeypatch):
    """When enabled, the client should attempt to call Perplexity API."""
    monkeypatch.setattr(settings, "AICMO_PERPLEXITY_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "PERPLEXITY_API_KEY", "dummy-key", raising=False)

    # Mock the httpx.Client to return a valid response
    import httpx
    from unittest.mock import Mock, MagicMock

    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": """{
                        "brand_summary": "Demo Brand is an active coffeehouse brand in Kolkata, India.",
                        "official_website": null,
                        "main_social_profiles": [],
                        "current_positioning": "Local coffeehouse leader",
                        "recent_content_themes": ["community", "quality"],
                        "local_competitors": [{"name": "Competitor A", "summary": "Local competitor"}],
                        "audience_pain_points": ["price sensitivity"],
                        "audience_language_snippets": ["Great coffee!"],
                        "hashtag_hints": ["#Coffee"]
                    }"""
                }
            }
        ]
    }
    mock_response.raise_for_status = Mock()

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client.post.return_value = mock_response

    monkeypatch.setattr(httpx, "Client", lambda timeout: mock_client)

    result = get_brand_research("Demo Brand", "Coffeehouse", "Kolkata, India")
    assert isinstance(result, BrandResearchResult)
    assert result.brand_summary is not None
    assert "Demo Brand" in (result.brand_summary or "")
    assert result.local_competitors  # mock returns some


def test_brand_research_missing_required_fields(monkeypatch):
    """Research should return None if brand_name or location is missing."""
    monkeypatch.setattr(settings, "AICMO_PERPLEXITY_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "PERPLEXITY_API_KEY", "dummy-key", raising=False)

    # Missing brand_name
    result = get_brand_research("", "Coffeehouse", "Kolkata, India")
    assert result is None

    # Missing location
    result = get_brand_research("Demo Brand", "Coffeehouse", "")
    assert result is None


def test_brand_research_caching(monkeypatch):
    """Verify that repeated calls use the cache (same result object)."""
    monkeypatch.setattr(settings, "AICMO_PERPLEXITY_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "PERPLEXITY_API_KEY", "dummy-key", raising=False)

    result1 = get_brand_research("Demo Brand", "Coffeehouse", "Kolkata, India")
    result2 = get_brand_research("Demo Brand", "Coffeehouse", "Kolkata, India")

    # Should be the same cached instance
    assert result1 is result2


def test_brand_brief_accepts_research():
    """BrandBrief should accept an optional research field."""
    from backend.generators.common_helpers import BrandBrief

    research = BrandResearchResult(
        brand_summary="Test summary",
        current_positioning="Local leader",
        local_competitors=[],
    )

    brand = BrandBrief(
        brand_name="Test Brand",
        industry="Coffeehouse",
        location="Kolkata",
        research=research,
    )

    assert brand.research is not None
    assert brand.research.brand_summary == "Test summary"


def test_brand_brief_works_without_research():
    """BrandBrief should work fine when research is None (backward compatibility)."""
    from backend.generators.common_helpers import BrandBrief

    brand = BrandBrief(
        brand_name="Test Brand",
        industry="Coffeehouse",
        location="Kolkata",
    )

    assert brand.research is None
