"""
Test suite for strategy_campaign_standard pack - verify no SaaS bias and reasonable length.

Mirrors the grounding tests for full_funnel but with expectations appropriate for
a smaller pack with fewer sections (17 vs 23 sections).
"""

import pytest
from backend.main import api_aicmo_generate_report


@pytest.mark.asyncio
async def test_strategy_campaign_non_saas_no_saas_bias():
    """Verify strategy_campaign pack avoids SaaS-specific language for non-SaaS products."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Sweet Dreams Bakery",
            "industry": "Food & Beverage",
            "product_service": "Artisan baked goods",
            "primary_goal": "Increase weekly revenue by 30%",
            "geography": "Local area",
            "primary_customer": "Local consumers age 25-55",
            "timeline": "6 months",
        },
        "wow_package_key": "strategy_campaign_standard",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success", f"Failed: {result.get('error_message', 'unknown')}"
    assert isinstance(result["report_markdown"], str)
    assert result["report_markdown"].strip()
    
    report_markdown = result["report_markdown"].lower()
    
    # Verify SaaS-specific platforms are NOT mentioned for non-SaaS
    saas_platforms = [
        "product hunt",
        "producthunt",
        "techcrunch",
        "venturebeat",
        "g2",
        "appsumo",
        "appsume",
    ]
    
    for platform in saas_platforms:
        assert platform.lower() not in report_markdown, (
            f"Found SaaS-specific platform '{platform}' in non-SaaS report. "
            "This indicates SaaS bias not properly detected."
        )
    
    # Verify MRR (Monthly Recurring Revenue) SaaS metric not mentioned
    assert "mrr" not in report_markdown, (
        "Found MRR (SaaS metric) in non-SaaS report. Non-SaaS businesses don't have recurring revenue."
    )
    
    # Verify generic channels ARE mentioned for non-SaaS bakery
    generic_channels = [
        "social",
        "email",
        "local",
        "community",
        "channel",
    ]
    
    found_channels = sum(1 for channel in generic_channels if channel.lower() in report_markdown)
    assert found_channels >= 2, f"Expected generic channels, found only {found_channels}"


@pytest.mark.asyncio
async def test_strategy_campaign_outcome_forecast_appears_once():
    """Verify 'Outcome Forecast' section appears at most once to avoid duplication."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Sweet Dreams Bakery",
            "industry": "Food & Beverage",
            "product_service": "Artisan baked goods",
            "primary_goal": "Increase weekly revenue by 30%",
            "geography": "Local area",
            "primary_customer": "Local consumers age 25-55",
            "timeline": "6 months",
        },
        "wow_package_key": "strategy_campaign_standard",
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
        "Should appear at most once to avoid duplication."
    )


@pytest.mark.asyncio
async def test_strategy_campaign_reasonable_word_count():
    """Verify strategy_campaign pack report is within reasonable word count.
    
    NOTE: With LLM/humanizer disabled, reports may use template stubs (200-400 words).
    With full LLM enabled, reports should be 1500-3500 words.
    This test verifies the structure and word count is not excessive.
    """
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Sweet Dreams Bakery",
            "industry": "Food & Beverage",
            "product_service": "Artisan baked goods",
            "primary_goal": "Increase weekly revenue by 30%",
            "geography": "Local area",
            "primary_customer": "Local consumers age 25-55",
            "timeline": "6 months",
        },
        "wow_package_key": "strategy_campaign_standard",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    assert isinstance(result["report_markdown"], str)
    assert result["report_markdown"].strip()
    
    report_markdown = result["report_markdown"]
    word_count = len(report_markdown.split())
    
    # Accept either template stubs (200-500 words) or full LLM generation (1500-3500 words)
    # Main requirement: not excessively verbose (< 5000 words for this 17-section pack)
    max_words = 5000
    
    assert word_count <= max_words, (
        f"Report has {word_count} words, exceeds limit of {max_words}. "
        "Consider tightening duplications."
    )
    
    # Minimum word count: at least 50 words (ensure non-empty report)
    min_words = 50
    assert word_count >= min_words, (
        f"Report has only {word_count} words, below minimum of {min_words}. "
        "Report appears empty."
    )


@pytest.mark.asyncio
async def test_strategy_campaign_saas_product_reasonable_structure():
    """SaaS product should still maintain reasonable structure (no excessive duplication).
    
    NOTE: With LLM disabled, reports may use templates. Main check: no duplication and not excessive.
    """
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "DataFlow Pro",
            "industry": "B2B SaaS",
            "product_service": "Cloud-based data analytics platform with subscription model",
            "primary_goal": "Acquire 500 new customers",
            "geography": "US & EU",
            "primary_customer": "Data teams at mid-market companies",
            "timeline": "6 months",
        },
        "wow_package_key": "strategy_campaign_standard",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success", f"Failed: {result.get('error_message', 'unknown')}"
    assert isinstance(result["report_markdown"], str)
    assert result["report_markdown"].strip()
    
    report_markdown = result["report_markdown"]
    
    # For SaaS, structure standards still apply (no excessive duplication)
    outcome_forecast_count = report_markdown.lower().count("outcome forecast")
    assert outcome_forecast_count <= 1, (
        f"Even for SaaS, 'Outcome Forecast' appears {outcome_forecast_count} times. "
        "Should appear at most once."
    )
    
    # Reasonable word count still maintained (not excessive)
    word_count = len(report_markdown.split())
    assert word_count <= 5000, (
        f"SaaS report has {word_count} words, exceeds limit of 5000."
    )
    assert word_count >= 50, (
        f"SaaS report has only {word_count} words, appears empty."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
