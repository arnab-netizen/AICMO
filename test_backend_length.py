#!/usr/bin/env python
"""Quick diagnostic script to test backend report generation."""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import aicmo_generate, GenerateRequest
from aicmo.io.client_reports import (
    ClientInputBrief,
    BrandBrief,
    AudienceBrief,
    GoalBrief,
    VoiceBrief,
    ProductServiceBrief,
    AssetsConstraintsBrief,
    OperationsBrief,
    StrategyExtrasBrief,
    generate_output_report_markdown,
)


async def test_full_generation():
    """Test full report generation and measure output size."""

    # Create a test brief
    brief = ClientInputBrief(
        brand=BrandBrief(
            brand_name="Diwali Delights",
            industry="Food & Beverage",
        ),
        audience=AudienceBrief(
            primary_customer="Urban professionals aged 25-45",
            secondary_customer="Families looking for premium food options",
        ),
        goal=GoalBrief(
            primary_goal="Increase brand awareness and online orders",
            timeline="30 days",
        ),
        voice=VoiceBrief(
            tone_of_voice=["modern", "festive", "authentic"],
        ),
        product_service=ProductServiceBrief(),
        assets_constraints=AssetsConstraintsBrief(
            focus_platforms=["Instagram", "Facebook", "TikTok"],
        ),
        operations=OperationsBrief(),
        strategy_extras=StrategyExtrasBrief(
            brand_adjectives=["premium", "authentic", "festive"],
        ),
    )

    # Create request for "Strategy + Campaign Pack" (standard)
    req = GenerateRequest(
        brief=brief,
        generate_marketing_plan=True,
        generate_campaign_blueprint=True,
        generate_social_calendar=True,
        generate_performance_review=False,
        generate_creatives=True,
        package_preset="Strategy + Campaign Pack (Standard)",
        include_agency_grade=True,
        use_learning=False,
        wow_enabled=False,
    )

    print("\n" + "=" * 80)
    print("🧪 TESTING FULL REPORT GENERATION")
    print("=" * 80)

    # Generate report
    report = await aicmo_generate(req)

    # Convert to markdown
    report_markdown = generate_output_report_markdown(brief, report)

    # Log the length
    print("\n✅ Report generation complete!")
    print(f"   Total markdown length: {len(report_markdown)} characters")
    print("\n   Last 600 characters of report:")
    print("   " + "-" * 76)
    tail = report_markdown[-600:] if len(report_markdown) > 600 else report_markdown
    for line in tail.split("\n"):
        print(f"   {line}")
    print("   " + "-" * 76)

    # Check for key sections
    sections = [
        ("Executive Summary", "Executive Summary" in report_markdown),
        ("Strategy", "## 2.3 Strategy" in report_markdown),
        ("Campaign Blueprint", "## 3. Campaign Blueprint" in report_markdown),
        ("Content Calendar", "## 4. Content Calendar" in report_markdown),
        ("Creatives", "## 7. Creatives" in report_markdown),
        ("Action Plan", "## 6. Next 30 days" in report_markdown),
    ]

    print("\n📊 Section check:")
    for section_name, present in sections:
        status = "✅" if present else "❌"
        print(f"   {status} {section_name}")

    return len(report_markdown)


if __name__ == "__main__":
    size = asyncio.run(test_full_generation())
    print(f"\n✅ Total report size: {size} characters\n")
