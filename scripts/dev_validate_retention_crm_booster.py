#!/usr/bin/env python3
"""
Dev validation script for retention_crm_booster pack.

Quick check during development to ensure pack generates without errors.
Follows pattern from dev_validate_launch_gtm_pack.py.

Usage:
    python scripts/dev_validate_retention_crm_booster.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Force stub mode for fast testing
os.environ["AICMO_STUB_MODE"] = "1"
os.environ["AICMO_USE_LLM"] = "false"

import asyncio
from backend.main import GenerateRequest, aicmo_generate
from aicmo.io.client_reports import (
    BrandBrief,
    AudienceBrief,
    GoalBrief,
    VoiceBrief,
    ProductServiceBrief,
    AssetsConstraintsBrief,
    OperationsBrief,
    StrategyExtrasBrief,
    ClientInputBrief,
)


def create_retention_crm_brief():
    """Create minimal brief for retention_crm_booster validation."""
    brand = BrandBrief(
        brand_name="RetentionTest",
        industry="D2C Subscription",
        founding_year=2021,
        location="US",
        product_service="Monthly subscription box service",
        primary_goal="Increase customer retention and lifetime value",
        primary_customer="Subscription customers seeking convenience and personalization",
        value_proposition="Curated products delivered monthly with personalized selections",
    )

    audience = AudienceBrief(
        primary_customer="Subscription customers (25-45) seeking curated discovery",
        secondary_customer="Gift givers and corporate buyers",
        demographics="Urban professionals, high disposable income, tech-savvy",
        behaviors="Monthly box subscribers, high engagement with personalization",
        platforms=["Email", "SMS", "Mobile App"],
    )

    goal = GoalBrief(
        primary_goal="Increase 90-day retention from 40% to 60% and grow LTV by 35%",
        secondary_goal="Reduce churn rate and increase referral rate",
        timeline="90 days",
        kpis=["Retention rate", "Churn rate", "LTV", "NPS"],
    )

    voice = VoiceBrief(
        adjectives=["Premium", "Personal", "Trustworthy"],
        tone="Warm, professional, customer-centric",
        personality="Helpful advisor focused on customer success",
    )

    product_service = ProductServiceBrief(
        offerings=[
            "Monthly subscription boxes",
            "Add-on products",
            "Gift subscriptions",
        ],
        value_proposition="Curated discovery with personalization",
        usp="AI-powered product matching based on preferences and feedback",
    )

    assets_constraints = AssetsConstraintsBrief(
        existing_content=["Product photos", "Customer testimonials", "Unboxing videos"],
        brand_assets=["Logo", "Brand colors", "Photography style guide"],
        constraints=[
            "Must maintain premium positioning",
            "Avoid discount-heavy messaging",
        ],
    )

    operations = OperationsBrief(
        team_size="5-10",
        tools=["Klaviyo", "Attentive", "Shopify", "Recharge"],
        budget="$50K-100K annually for CRM automation",
    )

    strategy_extras = StrategyExtrasBrief(
        brand_adjectives=["Premium", "Personalized", "Reliable"],
        negative_constraints="Avoid generic promotional language, mass-market positioning",
        agency_notes="Focus on lifecycle automation and personalization at scale",
    )

    return ClientInputBrief(
        brand=brand,
        audience=audience,
        goal=goal,
        voice=voice,
        product_service=product_service,
        assets_constraints=assets_constraints,
        operations=operations,
        strategy_extras=strategy_extras,
    )


async def main():
    print("\n" + "=" * 70)
    print("DEV VALIDATION: retention_crm_booster")
    print("=" * 70)

    brief = create_retention_crm_brief()
    print(f"\n✓ Brief created: {brief.brand.brand_name}")

    # Create request - no WOW for direct section testing
    req = GenerateRequest(
        brief=brief,
        package_preset="retention_crm_booster",
        wow_package_key=None,  # Test sections directly
        skip_benchmark_enforcement=False,  # Enforce benchmarks
        sections_preset="retention_crm_booster",
    )

    print("🔄 Generating pack with benchmark enforcement...")

    try:
        output = await aicmo_generate(req)

        if output.extra_sections:
            section_count = len(output.extra_sections)
            total_words = sum(len(content.split()) for content in output.extra_sections.values())
            print(f"\n✅ SUCCESS: Generated {section_count} sections ({total_words:,} words)")
            print("\nSections generated:")
            for section_title in output.extra_sections.keys():
                print(f"  - {section_title}")
        else:
            print("\n⚠️  Warning: No sections in extra_sections")

        print("\n✅ Validation passed - pack is client-ready")
        return 0

    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}")
        print(f"   {str(e)[:200]}")
        print("\n💡 This means benchmark enforcement caught quality issues.")
        print("   Run full test: python test_retention_crm_booster.py")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
