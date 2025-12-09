"""
Test suite for full_funnel_growth_suite pack - verify no SaaS bias and reasonable length.
"""

import pytest
from backend.main import api_aicmo_generate_report
from aicmo.io.client_reports import (
    ClientInputBrief,
    BrandBrief,
    AudienceBrief,
    GoalBrief,
    VoiceBrief,
    ProductServiceBrief,
    ProductServiceItem,
    OperationsBrief,
    AssetsConstraintsBrief,
    StrategyExtrasBrief,
)


@pytest.fixture
def generic_non_saas_brief():
    """Create a minimal generic (non-SaaS) brief for testing."""
    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="Local Bakery Chain",
            industry="Food & Beverage",
            product_service="Artisan bread and pastries",
            primary_goal="Increase foot traffic and online orders",
            primary_customer="Local families and professionals",
            location="Northeast US",
            timeline=None,
            business_type="Retail",
            description="Community-focused bakery chain with 5 locations",
        ),
        audience=AudienceBrief(
            primary_customer="Local families aged 25-55",
            pain_points=["Limited awareness of local bakery brand", "Inconsistent product availability"],
        ),
        goal=GoalBrief(
            primary_goal="Increase foot traffic 30% and online orders 50%",
            timeline="6 months",
            kpis=["Monthly foot traffic", "Online order volume", "Customer retention"],
        ),
        voice=VoiceBrief(tone_of_voice=["Friendly", "Local", "Reliable"]),
        product_service=ProductServiceBrief(
            items=[ProductServiceItem(name="Artisan Bread", usp="Fresh daily, local grains")]
        ),
        operations=OperationsBrief(budget_range="$5K-$15K", timeline_months=6, team_size=None),
        assets_constraints=AssetsConstraintsBrief(existing_assets=[], constraints=[]),
        strategy_extras=StrategyExtrasBrief(unique_angles=[], learning_from_previous=[]),
    )


@pytest.mark.asyncio
async def test_full_funnel_no_saas_bias_non_saas_brief(generic_non_saas_brief):
    """Verify full_funnel pack avoids SaaS-specific language for non-SaaS products."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Local Bakery Chain",
            "industry": "Food & Beverage",
            "product_service": "Artisan bread and pastries",
            "primary_goal": "Increase foot traffic and online orders",
            "geography": "Northeast US",
            "primary_customer": "Local families aged 25-55",
            "timeline": "6 months",
        },
        "pack_key": "full_funnel_growth_suite",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    assert isinstance(result["report_markdown"], str)
    assert result["report_markdown"].strip()
    
    report_markdown = result["report_markdown"].lower()
    
    # Verify SaaS-specific platforms are NOT mentioned for non-SaaS
    saas_platforms = [
        "product hunt",
        "producthunt",
        "techcrunch",
        "ventureBeat",
        "g2",
        "appsume",
        "appsumo",
        "slack community",  # SaaS-specific
    ]
    
    for platform in saas_platforms:
        assert platform.lower() not in report_markdown, (
            f"Found SaaS-specific platform '{platform}' in non-SaaS report. "
            "This indicates SaaS bias not properly detected."
        )
    
    # Verify generic channels ARE mentioned
    generic_channels = [
        "social media",
        "email",
        "search",
        "content",
        "partnership",
        "industry",
    ]
    
    found_channels = sum(1 for channel in generic_channels if channel.lower() in report_markdown)
    assert found_channels >= 3, f"Expected generic channels, found only {found_channels}"


@pytest.mark.asyncio
async def test_full_funnel_outcome_forecast_appears_once(generic_non_saas_brief):
    """Verify 'Outcome Forecast' section appears at most once to avoid duplication."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Local Bakery Chain",
            "industry": "Food & Beverage",
            "product_service": "Artisan bread and pastries",
            "primary_goal": "Increase foot traffic and online orders",
            "geography": "Northeast US",
            "primary_customer": "Local families aged 25-55",
            "timeline": "6 months",
        },
        "pack_key": "full_funnel_growth_suite",
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
async def test_full_funnel_reasonable_word_count(generic_non_saas_brief):
    """Verify full_funnel pack report stays below reasonable word count."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Local Bakery Chain",
            "industry": "Food & Beverage",
            "product_service": "Artisan bread and pastries",
            "primary_goal": "Increase foot traffic and online orders",
            "geography": "Northeast US",
            "primary_customer": "Local families aged 25-55",
            "timeline": "6 months",
        },
        "pack_key": "full_funnel_growth_suite",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    assert isinstance(result["report_markdown"], str)
    assert result["report_markdown"].strip()
    
    report_markdown = result["report_markdown"]
    word_count = len(report_markdown.split())
    
    # Full funnel premium pack should be comprehensive but not excessive
    # Target: 4500-5500 words (roughly 25-35 page document)
    # NOTE: With 23 sections in full_funnel pack, some length is expected
    max_words = 5500
    
    assert word_count <= max_words, (
        f"Report has {word_count} words, exceeds limit of {max_words}. "
        "Consider tightening strategy section duplications."
    )
    
    # Also ensure it's not too short (should be substantial)
    min_words = 2000
    assert word_count >= min_words, (
        f"Report has only {word_count} words, below minimum of {min_words}. "
        "Report may be too sparse."
    )


@pytest.mark.asyncio
async def test_full_funnel_execution_roadmap_concise(generic_non_saas_brief):
    """Verify execution_roadmap section is concise and avoids excessive length."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Local Bakery Chain",
            "industry": "Food & Beverage",
            "product_service": "Artisan bread and pastries",
            "primary_goal": "Increase foot traffic and online orders",
            "geography": "Northeast US",
            "primary_customer": "Local families aged 25-55",
            "timeline": "6 months",
        },
        "pack_key": "full_funnel_growth_suite",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    assert isinstance(result["report_markdown"], str)
    assert result["report_markdown"].strip()
    
    report_markdown = result["report_markdown"]
    
    # Extract execution roadmap section (rough extraction)
    if "execution roadmap" in report_markdown.lower():
        roadmap_start = report_markdown.lower().find("execution roadmap")
        roadmap_section = report_markdown[roadmap_start:roadmap_start+2000]  # Approx 2000 chars
        
        # Count Phase/milestone headers (should be 3-5, not 10+)
        phase_count = roadmap_section.count("##")
        
        assert phase_count <= 6, (
            f"Execution roadmap has {phase_count} major sections. "
            "Should be concise with 3-5 major phases, not overly detailed."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
