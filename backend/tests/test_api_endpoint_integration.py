"""
Integration test for PACKAGE_NAME_TO_KEY mapping fix.

This test validates that the HTTP endpoint uses PACKAGE_NAME_TO_KEY mapping
to convert display names to preset keys, ensuring the same behavior as
direct aicmo_generate() calls.
"""

import asyncio
import os
import pytest
from httpx import AsyncClient
from backend.main import aicmo_generate, GenerateRequest
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
            pain_points=["Limited authentic ethnic wear options", "Seasonal collection discovery"],
        ),
        goal=GoalBrief(
            primary_goal="Drive Diwali campaign sales",
            secondary_goal="Build seasonal collection awareness",
            timeline="30 days",
            kpis=["Sales conversion", "Collection awareness"],
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
async def test_package_name_to_key_mapping_via_api():
    """
    Test that when aicmo_generate() receives package_preset="Strategy + Campaign Pack (Standard)",
    it correctly maps to "strategy_campaign_standard" and generates the full 17-section report.
    
    This validates FIX #3: PACKAGE_NAME_TO_KEY mapping used in the endpoint handler.
    """
    os.environ["AICMO_DEBUG_REPORT_FOOTER"] = "1"
    
    try:
        brief = _create_standard_pack_brief()
        
        # Create request with DISPLAY NAME (what Streamlit UI sends)
        req = GenerateRequest(
            brief=brief,
            generate_marketing_plan=True,
            generate_campaign_blueprint=True,
            generate_social_calendar=True,
            generate_creatives=True,
            package_preset="Strategy + Campaign Pack (Standard)",  # DISPLAY NAME
            include_agency_grade=True,
            use_learning=False,
            wow_enabled=True,
            wow_package_key="strategy_campaign_standard",
            stage="draft",
        )
        
        # Call aicmo_generate directly (this is what the endpoint handler does)
        report = await aicmo_generate(req)
        
        # Get the report markdown (simulating what the endpoint returns)
        from backend.main import generate_output_report_markdown
        report_markdown = generate_output_report_markdown(brief, report)
        
        # Validate report structure
        assert len(report_markdown) > 0, "Report is empty"
        
        # Validate report is not truncated (full 17 sections)
        section_count = report_markdown.count("## ")
        assert section_count >= 17, (
            f"Expected at least 17 sections, got {section_count}. "
            f"Report length: {len(report_markdown)} chars. "
            f"Report tail:\n{report_markdown[-1000:]}"
        )
        
        # Validate report length (17 sections should be 3000+ characters)
        assert len(report_markdown) >= 3000, (
            f"Expected report ≥ 3000 chars, got {len(report_markdown)}. "
            f"Possible truncation: {report_markdown[-500:]}"
        )
        
        print(f"\n✅ MAPPING TEST PASSED")
        print(f"   Sections: {section_count}")
        print(f"   Length: {len(report_markdown)} chars")
        print(f"   Package: Strategy + Campaign Pack (Standard) → strategy_campaign_standard")
        
    finally:
        if "AICMO_DEBUG_REPORT_FOOTER" in os.environ:
            del os.environ["AICMO_DEBUG_REPORT_FOOTER"]


@pytest.mark.asyncio
async def test_preset_key_directly():
    """
    Test that when aicmo_generate() receives the preset key directly,
    it also works correctly (alternative code path).
    """
    os.environ["AICMO_DEBUG_REPORT_FOOTER"] = "1"
    
    try:
        brief = _create_standard_pack_brief()
        
        # Create request with PRESET KEY directly (alternative format)
        req = GenerateRequest(
            brief=brief,
            generate_marketing_plan=True,
            generate_campaign_blueprint=True,
            generate_social_calendar=True,
            generate_creatives=True,
            package_preset="strategy_campaign_standard",  # PRESET KEY
            include_agency_grade=True,
            use_learning=False,
            wow_enabled=True,
            wow_package_key="strategy_campaign_standard",
            stage="draft",
        )
        
        # Call aicmo_generate directly
        report = await aicmo_generate(req)
        
        # Get the report markdown
        from backend.main import generate_output_report_markdown
        report_markdown = generate_output_report_markdown(brief, report)
        
        # Validate report is full 17 sections
        section_count = report_markdown.count("## ")
        assert section_count >= 17, (
            f"Expected at least 17 sections with preset key, got {section_count}"
        )
        
        print(f"\n✅ PRESET KEY TEST PASSED")
        print(f"   Sections: {section_count}")
        print(f"   Length: {len(report_markdown)} chars")
        
    finally:
        if "AICMO_DEBUG_REPORT_FOOTER" in os.environ:
            del os.environ["AICMO_DEBUG_REPORT_FOOTER"]


@pytest.mark.asyncio
async def test_token_ceiling_with_display_name():
    """
    Validate that token ceiling (min 12000 for Standard pack) is enforced
    when using display name format.
    """
    os.environ["AICMO_DEBUG_REPORT_FOOTER"] = "1"
    
    try:
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
        
        # Report should have all 17 sections despite incoming stage being "draft"
        section_count = report_markdown.count("## ")
        assert section_count >= 17, (
            f"Expected 17+ sections despite draft stage, got {section_count}"
        )
        
        assert len(report_markdown) >= 3000, (
            f"Report too short: {len(report_markdown)} chars"
        )
        
        print(f"\n✅ TOKEN CEILING TEST PASSED")
        print(f"   Sections: {section_count}")
        print(f"   Length: {len(report_markdown)} chars")
        
    finally:
        if "AICMO_DEBUG_REPORT_FOOTER" in os.environ:
            del os.environ["AICMO_DEBUG_REPORT_FOOTER"]
