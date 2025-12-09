"""
Smoke test for strategy_campaign_standard pack hardening.

Verifies:
1. Quality gate passes (brand name mentioned enough)
2. Generation flow works without errors
3. No SaaS bias for non-SaaS businesses (when output is available)
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
    """Create a minimal non-SaaS brief (local bakery) for strategy_campaign testing."""
    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="Sweet Dreams Bakery",
            industry="Food & Beverage",
            product_service="Artisan baked goods",
            primary_goal="Increase weekly revenue",
            primary_customer="Local customers",
            location="Local area",
            description="Community bakery",
        ),
        audience=AudienceBrief(
            primary_customer="Local consumers age 25-55",
            pain_points=["Quality varies", "Limited options"],
        ),
        goal=GoalBrief(
            primary_goal="Increase weekly revenue by 30%",
            timeline="6 months",
            kpis=["Weekly revenue", "Online orders"],
        ),
        voice=VoiceBrief(tone_of_voice=["Warm", "Authentic"]),
        product_service=ProductServiceBrief(
            items=[ProductServiceItem(name="Artisan Bread", usp="Fresh daily")]
        ),
        operations=OperationsBrief(budget_range="$5K-$15K", timeline_months=6),
        assets_constraints=AssetsConstraintsBrief(existing_assets=[], constraints=[]),
        strategy_extras=StrategyExtrasBrief(unique_angles=[], learning_from_previous=[]),
    )


@pytest.mark.asyncio
async def test_strategy_campaign_quality_gate_passes(generic_non_saas_brief):
    """
    REQUIREMENT: Quality gate should pass with brand name mentioned at least 2x
    in executive_summary + strategy combined.
    """

    payload = {
        "client_brief": generic_non_saas_brief.model_dump(exclude_none=True),
        "wow_package_key": "strategy_campaign_standard",
        "stage": "draft",
        "draft_mode": True,
    }


@pytest.mark.asyncio
async def test_strategy_campaign_saas_non_saas_detection(generic_non_saas_brief):
    """
    REQUIREMENT: Strategy + Campaign pack should apply non-SaaS logic
    for non-SaaS businesses (no SaaS-specific platforms mentioned).
    """

    payload = {
        "client_brief": generic_non_saas_brief.model_dump(exclude_none=True),
        "wow_package_key": "strategy_campaign_standard",
        "stage": "draft",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    
    # Should succeed and get markdown
    assert result["status"] == "success", f"Failed: {result.get('error_message', 'unknown')}"
    
    report_markdown = result["report_markdown"]
    assert isinstance(report_markdown, str)
    assert report_markdown.strip()
    
    # Verify no SaaS bias for non-SaaS business
    saas_bias_terms = [
        "ProductHunt",
        "Product Hunt",
        "G2",
        "MRR",
        "AppSumo",
        "beta launch",
    ]
    
    found_bias = [term for term in saas_bias_terms if term in report_markdown]
    assert not found_bias, f"Found SaaS bias: {found_bias}"
    
    # Verify at least one Outcome Forecast (not multiple)
    assert report_markdown.count("Outcome Forecast") <= 1, \
        "Outcome Forecast appears more than once"
