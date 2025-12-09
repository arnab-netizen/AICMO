"""
Test suite for quick_social_basic pack - verify no SaaS bias and reasonable length.

Mirrors the grounding tests for strategy_campaign but with expectations
appropriate for a lighter, social-focused pack (8 sections vs 17 sections).
"""

import pytest
from backend.main import api_aicmo_generate_report


@pytest.mark.asyncio
async def test_quick_social_non_saas_no_saas_bias():
    """Verify quick_social pack avoids SaaS-specific language for non-SaaS products."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Morning Brew Cafe",
            "industry": "Coffee Shop",
            "product_service": "Specialty coffee and pastries",
            "primary_goal": "Increase foot traffic by 30%",
            "geography": "Local area",
            "primary_customer": "Local professionals and students",
            "timeline": "30 days",
        },
        "wow_package_key": "quick_social_basic",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success", f"Failed: {result.get('error_message', 'unknown')}"
    assert isinstance(result["report_markdown"], str)
    assert result["report_markdown"].strip()
    
    report_markdown = result["report_markdown"].lower()
    
    # Verify SaaS-specific metrics are NOT mentioned for non-SaaS
    # Use word boundaries to avoid false positives (e.g., "narrative" contains "arr")
    import re
    
    saas_metrics = [
        (r"\bMRR\b", "Monthly Recurring Revenue"),
        (r"\bARR\b", "Annual Recurring Revenue"),  # Word boundary to avoid "narrative", "array"
        (r"churn rate", "churn rate"),
        (r"customer acquisition cost", "customer acquisition cost"),
        (r"\bCAC\b", "Customer Acquisition Cost"),
        (r"\bLTV\b", "Lifetime Value"),
        (r"pricing tier", "pricing tier"),
        (r"subscription", "subscription"),
    ]
    
    for pattern, name in saas_metrics:
        if re.search(pattern, report_markdown):
            raise AssertionError(
                f"Found SaaS metric '{name}' ({pattern}) in non-SaaS social report. "
                "This indicates SaaS bias not properly detected."
            )
    
    # Verify social platforms ARE mentioned for coffee shop
    social_platforms = [
        "instagram",
        "tiktok",
        "facebook",
        "social",
    ]
    
    found_platforms = sum(1 for platform in social_platforms if platform.lower() in report_markdown)
    assert found_platforms >= 1, f"Expected social platforms, found only {found_platforms}"


@pytest.mark.asyncio
async def test_quick_social_outcome_forecast_appears_once():
    """Verify 'Outcome Forecast' section appears at most once."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Morning Brew Cafe",
            "industry": "Coffee Shop",
            "product_service": "Specialty coffee and pastries",
            "primary_goal": "Increase foot traffic by 30%",
            "geography": "Local area",
            "primary_customer": "Local professionals and students",
            "timeline": "30 days",
        },
        "wow_package_key": "quick_social_basic",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    assert isinstance(result["report_markdown"], str)
    assert result["report_markdown"].strip()
    
    report_markdown = result["report_markdown"]
    
    # Count occurrences (case-insensitive)
    outcome_forecast_count = report_markdown.lower().count("outcome forecast")
    
    assert outcome_forecast_count <= 1, (
        f"'Outcome Forecast' appears {outcome_forecast_count} times. "
        "Should appear at most once."
    )


@pytest.mark.asyncio
async def test_quick_social_reasonable_word_count():
    """Verify quick_social pack report is within reasonable word count.
    
    NOTE: With LLM disabled, reports use template stubs (200-400 words).
    With full LLM enabled, reports should be 1000-3000 words (lighter than strategy_campaign).
    """
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Morning Brew Cafe",
            "industry": "Coffee Shop",
            "product_service": "Specialty coffee and pastries",
            "primary_goal": "Increase foot traffic by 30%",
            "geography": "Local area",
            "primary_customer": "Local professionals and students",
            "timeline": "30 days",
        },
        "wow_package_key": "quick_social_basic",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    assert isinstance(result["report_markdown"], str)
    assert result["report_markdown"].strip()
    
    report_markdown = result["report_markdown"]
    word_count = len(report_markdown.split())
    
    # Quick Social is lighter than strategy_campaign, so lower word limit
    # Accept either template stubs (200-400 words) or full LLM generation (1000-3000 words)
    max_words = 4000
    
    assert word_count <= max_words, (
        f"Report has {word_count} words, exceeds limit of {max_words}. "
        "Report appears too verbose."
    )
    
    # Minimum word count: at least 50 words (ensure non-empty report)
    min_words = 50
    assert word_count >= min_words, (
        f"Report has only {word_count} words, below minimum of {min_words}. "
        "Report appears incomplete."
    )


@pytest.mark.asyncio
async def test_quick_social_social_focus_not_enterprise():
    """Verify quick_social pack focuses on social platforms, not enterprise B2B."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Morning Brew Cafe",
            "industry": "Coffee Shop",
            "product_service": "Specialty coffee and pastries",
            "primary_goal": "Increase foot traffic by 30%",
            "geography": "Local area",
            "primary_customer": "Local professionals and students",
            "timeline": "30 days",
        },
        "wow_package_key": "quick_social_basic",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    assert isinstance(result["report_markdown"], str)
    assert result["report_markdown"].strip()
    
    report_markdown = result["report_markdown"].lower()
    
    # Should mention content calendar, posts, engagement (social terms)
    social_terms = [
        "post",
        "content",
        "engagement",
        "calendar",
        "hashtag",
    ]
    
    found_terms = sum(1 for term in social_terms if term.lower() in report_markdown)
    assert found_terms >= 2, (
        f"Expected multiple social-focused terms, found only {found_terms}. "
        "Report may be missing social focus."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
