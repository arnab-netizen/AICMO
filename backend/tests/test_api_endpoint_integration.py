"""
Integration test for HTTP endpoint fix.

This test validates that the HTTP endpoint (used by Streamlit UI) now calls
the SAME core generator logic that the unit tests use, producing full 17-section
reports for Strategy + Campaign Pack (Standard).

The key fix: The endpoint now builds a complete ClientInputBrief from the
flattened Streamlit payload instead of trying to create an incomplete one.
"""

import os
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app, aicmo_generate, GenerateRequest
from aicmo.io.client_reports import (
    ClientInputBrief,
    BrandBrief,
    AudienceBrief,
    GoalBrief,
    VoiceBrief,
    ProductServiceBrief,
    ProductServiceItem,
    AssetsConstraintsBrief,
    OperationsBrief,
    StrategyExtrasBrief,
)


@pytest.mark.asyncio
async def test_http_endpoint_strategy_campaign_standard_full_report():
    """
    Test that the HTTP endpoint returns full 17-section report
    when given Strategy + Campaign Pack (Standard) payload.

    This validates that the endpoint now:
    1. Builds a complete ClientInputBrief from flattened Streamlit data
    2. Uses PACKAGE_NAME_TO_KEY mapping to resolve display name to preset key
    3. Applies effective_stage override (draft → final)
    4. Applies token ceiling (12000 minimum)
    5. Calls the same aicmo_generate() core function as tests
    """
    os.environ["AICMO_DEBUG_REPORT_FOOTER"] = "1"

    try:
        # Build payload EXACTLY like Streamlit sends it
        payload = {
            "stage": "draft",
            "client_brief": {
                "raw_brief_text": (
                    "Women's ethnic wear boutique offering fusion fashion items. "
                    "Target: fashion-conscious women 25-45. "
                    "Goal: Drive Diwali campaign sales. "
                    "Budget: $25K-50K. Timeline: 30 days."
                ),
                "client_name": "Fashion Forward",
                "brand_name": "StyleHub",
                "product_service": "Women's ethnic wear boutique offering fusion fashion items",
                "industry": "Fashion & Retail",
                "geography": "USA",
                "objectives": "Increase brand awareness and customer engagement",
                "budget": "$25,000 - $50,000",
                "timeline": "3-6 months",
                "constraints": "Limited in-house team",
            },
            "services": {
                "include_agency_grade": True,
                "marketing_plan": True,
                "campaign_blueprint": True,
                "social_calendar": True,
                "performance_review": False,
                "creatives": True,
            },
            "package_name": "Strategy + Campaign Pack (Standard)",  # Display name
            "wow_enabled": True,
            "wow_package_key": "strategy_campaign_standard",
            "refinement_mode": {
                "name": "Balanced",
                "passes": 1,
                "max_tokens": 6000,
                "temperature": 0.7,
            },
            "feedback": "",
            "previous_draft": "",
            "learn_items": [],
            "use_learning": False,
            "industry_key": None,
        }

        # Call the HTTP endpoint via test client
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/aicmo/generate_report", json=payload)

        # Validate response structure
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Error: {response.text}"
        )
        result = response.json()
        assert "report_markdown" in result, "Missing report_markdown in response"
        assert result["status"] == "success", f"Status is {result.get('status')}, not success"

        report_markdown = result["report_markdown"]

        # Validate report is FULL 17 sections
        section_count = report_markdown.count("## ")
        assert section_count >= 17, (
            f"Expected at least 17 sections, got {section_count}. "
            f"Report length: {len(report_markdown)} chars."
        )

        # Validate report length
        assert len(report_markdown) >= 3000, (
            f"Expected report ≥ 3000 chars, got {len(report_markdown)}."
        )

        # Validate debug footer shows correct values
        assert "DEBUG FOOTER (HTTP ENDPOINT PATH)" in report_markdown
        assert "strategy_campaign_standard" in report_markdown
        assert "Effective Stage" in report_markdown and "final" in report_markdown
        assert "Effective Max Tokens" in report_markdown and "12000" in report_markdown

        print(f"\n✅ HTTP ENDPOINT TEST PASSED")
        print(f"   Sections: {section_count}")
        print(f"   Length: {len(report_markdown)} chars")

    finally:
        if "AICMO_DEBUG_REPORT_FOOTER" in os.environ:
            del os.environ["AICMO_DEBUG_REPORT_FOOTER"]


@pytest.mark.asyncio
async def test_http_endpoint_full_report_without_debug_footer():
    """
    Test HTTP endpoint without debug footer (production mode).
    """
    if "AICMO_DEBUG_REPORT_FOOTER" in os.environ:
        del os.environ["AICMO_DEBUG_REPORT_FOOTER"]

    payload = {
        "stage": "draft",
        "client_brief": {
            "raw_brief_text": "Women's ethnic wear boutique. Goal: Diwali campaign.",
            "brand_name": "StyleHub",
            "product_service": "Women's ethnic wear",
            "industry": "Fashion & Retail",
            "timeline": "30 days",
        },
        "services": {
            "include_agency_grade": True,
            "marketing_plan": True,
            "campaign_blueprint": True,
            "social_calendar": True,
            "creatives": True,
        },
        "package_name": "Strategy + Campaign Pack (Standard)",
        "wow_enabled": True,
        "wow_package_key": "strategy_campaign_standard",
        "refinement_mode": {"name": "Balanced", "max_tokens": 6000},
        "use_learning": False,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/aicmo/generate_report", json=payload)

    assert response.status_code == 200
    result = response.json()
    report_markdown = result["report_markdown"]

    # Should NOT have debug footer
    assert "DEBUG FOOTER" not in report_markdown

    # But should still have full report
    section_count = report_markdown.count("## ")
    assert section_count >= 17, f"Expected 17+ sections, got {section_count}"

    print(f"\n✅ PRODUCTION MODE TEST PASSED")
    print(f"   Sections: {section_count}")


@pytest.mark.asyncio
async def test_http_endpoint_token_ceiling_enforced():
    """
    Test that token ceiling (minimum 12000 for Standard pack) is enforced.
    """
    os.environ["AICMO_DEBUG_REPORT_FOOTER"] = "1"

    try:
        payload = {
            "stage": "draft",
            "client_brief": {
                "raw_brief_text": "Women's ethnic wear. Goal: Diwali sales.",
                "brand_name": "StyleHub",
                "product_service": "Women's ethnic wear",
                "industry": "Fashion & Retail",
            },
            "services": {
                "include_agency_grade": True,
                "marketing_plan": True,
                "campaign_blueprint": True,
                "social_calendar": True,
                "creatives": True,
            },
            "package_name": "Strategy + Campaign Pack (Standard)",
            "wow_enabled": True,
            "wow_package_key": "strategy_campaign_standard",
            "refinement_mode": {
                "name": "Balanced",
                "max_tokens": 3000,  # LOW - should be forced to 12000
            },
            "use_learning": False,
        }

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/aicmo/generate_report", json=payload)

        assert response.status_code == 200
        report_markdown = response.json()["report_markdown"]

        # Verify token ceiling was enforced in footer
        assert "Effective Max Tokens" in report_markdown and "12000" in report_markdown
        section_count = report_markdown.count("## ")
        assert section_count >= 17

        print(f"\n✅ TOKEN CEILING TEST PASSED")
        print(f"   Effective max_tokens: 12000")

    finally:
        if "AICMO_DEBUG_REPORT_FOOTER" in os.environ:
            del os.environ["AICMO_DEBUG_REPORT_FOOTER"]


# Keep original direct aicmo_generate tests for validation
def _create_standard_pack_brief() -> ClientInputBrief:
    """Create a ClientInputBrief for testing the Standard pack."""
    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="Women's Ethnic Wear Boutique",
            industry="Fashion/Retail",
            business_type="B2C",
            description="Premium women's ethnic wear and seasonal collections",
        ),
        audience=AudienceBrief(
            primary_customer="Fashion-conscious women aged 25-45",
            pain_points=["Limited authentic ethnic wear options"],
        ),
        goal=GoalBrief(
            primary_goal="Drive Diwali campaign sales",
            timeline="30 days",
            kpis=["Sales conversion"],
        ),
        voice=VoiceBrief(
            tone_of_voice=["Elegant", "Traditional"],
        ),
        product_service=ProductServiceBrief(
            items=[
                ProductServiceItem(
                    name="Ethnic Wear Collection",
                    usp="Premium quality with traditional craftsmanship",
                )
            ],
        ),
        assets_constraints=AssetsConstraintsBrief(
            focus_platforms=["Instagram", "Facebook", "Pinterest"],
        ),
        operations=OperationsBrief(
            needs_calendar=True,
        ),
        strategy_extras=StrategyExtrasBrief(
            success_30_days="30% increase in Diwali collection orders",
            brand_adjectives=["elegant", "traditional", "premium"],
        ),
    )


@pytest.mark.asyncio
async def test_direct_generator_with_display_name():
    """
    Validate the direct aicmo_generate path with display name.
    This ensures both HTTP and direct paths work.
    """
    brief = _create_standard_pack_brief()

    req = GenerateRequest(
        brief=brief,
        generate_marketing_plan=True,
        generate_campaign_blueprint=True,
        generate_social_calendar=True,
        generate_creatives=True,
        package_preset="Strategy + Campaign Pack (Standard)",
        include_agency_grade=True,
        use_learning=False,
        wow_enabled=True,
        wow_package_key="strategy_campaign_standard",
        stage="draft",
    )

    report = await aicmo_generate(req)
    from backend.main import generate_output_report_markdown

    report_markdown = generate_output_report_markdown(brief, report)

    section_count = report_markdown.count("## ")
    assert section_count >= 17, f"Expected 17+ sections, got {section_count}"
    assert len(report_markdown) >= 3000

    print(f"\n✅ DIRECT GENERATOR TEST PASSED")
    print(f"   Sections: {section_count}")
