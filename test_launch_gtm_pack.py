#!/usr/bin/env python3
"""
Test suite for launch_gtm_pack validation.

Tests that all 13 sections of launch_gtm_pack:
- Generate real content (no stubs)
- Pass benchmark validation (0 errors required)
- Use proper heading structure (### for subsections)
- Include concrete tactics and examples

Reference: test_strategy_campaign_standard.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Force NON-STUB mode for realistic testing
os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-template-testing"
os.environ["AICMO_USE_LLM"] = "false"
os.environ["AICMO_PERPLEXITY_ENABLED"] = "false"
os.environ["AICMO_STUB_MODE"] = "0"

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
from backend.utils.wow_markdown_parser import parse_wow_markdown_to_sections
from backend.validators.report_gate import validate_report_sections
import asyncio


def create_test_brief() -> ClientInputBrief:
    """Create realistic brief for launch_gtm_pack testing."""
    brand = BrandBrief(
        brand_name="LaunchBox",
        industry="D2C - Consumer Tech",
        geography="United States (Austin, TX headquarters)",
        product_service="AI-powered product launch management platform for DTC brands",
        value_proposition="Execute flawless product launches with automated workflows, market intelligence, and real-time launch analytics that help consumer brands achieve 3x higher launch success rates",
        primary_goal="Launch LaunchBox 2.0 platform and acquire 1,000 paying customers in 90 days",
        primary_customer="Marketing Directors, Brand Managers, and Product Leads at DTC consumer brands with $5M-$50M annual revenue",
        secondary_customer="E-commerce Managers and Growth Marketers at emerging consumer brands seeking launch expertise",
        location="United States",
        timeline="90 days (Q1 2025)",
        brand_tone="Bold, innovative, results-driven, startup-friendly",
    ).with_safe_defaults()

    return ClientInputBrief(
        brand=brand,
        audience=AudienceBrief(
            primary_customer="Marketing Directors and Brand Managers at mid-market DTC brands ($5M-$50M revenue)",
            secondary_customer="E-commerce Managers and Growth Marketers at emerging consumer brands",
            pain_points=[
                "Product launches fail 60% of the time due to poor coordination across marketing, sales, and product teams",
                "Manual launch management via spreadsheets leads to missed deadlines and budget overruns",
                "No centralized platform to track launch metrics, market response, and ROI in real-time",
                "Competitive intelligence gathering takes 20+ hours per launch, often incomplete",
                "Launch playbooks are static docs that teams ignore or can't adapt to changing market conditions",
            ],
            online_hangouts=[
                "LinkedIn",
                "Instagram",
                "Twitter/X",
                "Reddit r/startups",
                "Product Hunt",
            ],
        ),
        goal=GoalBrief(
            primary_goal="Launch LaunchBox 2.0 and acquire 1,000 paying customers ($99/month tier) generating $100K MRR within 90 days",
            kpis=[
                "1,000 paid customers ($99/month tier)",
                "$100K monthly recurring revenue by day 90",
                "10,000 pre-launch waitlist signups",
                "Product Hunt #1 Product of the Day on launch day",
                "4.5+ G2 rating from first 100 customers",
            ],
            timeline="90 days (January-March 2025)",
        ),
        voice=VoiceBrief(tone_of_voice=["bold", "innovative", "data-driven", "startup-friendly"]),
        product_service=ProductServiceBrief(),
        assets_constraints=AssetsConstraintsBrief(
            focus_platforms=[
                "Instagram (launch stories + Reels)",
                "LinkedIn (B2B thought leadership)",
                "Product Hunt (launch day)",
                "Twitter/X (real-time launch updates)",
                "Email (nurture sequences)",
            ]
        ),
        operations=OperationsBrief(),
        strategy_extras=StrategyExtrasBrief(
            campaign_name="LaunchBox 2.0 Launch Campaign",
            brand_adjectives=[
                "innovative",
                "data-driven",
                "launch-obsessed",
                "results-focused",
                "agile",
            ],
        ),
    )


async def main():
    """Test all 13 launch_gtm_pack sections for validation compliance."""
    print("\n" + "=" * 70)
    print("LAUNCH_GTM_PACK VALIDATION TEST")
    print("=" * 70)

    # Step 1: Create test brief
    print("\n📋 Creating test brief...")
    brief = create_test_brief()
    print(f"   Brand: {brief.brand.brand_name}")
    print(f"   Goal: {brief.goal.primary_goal}")
    print("   Pack: launch_gtm_pack")

    # Step 2: Generate full pack
    print("\n" + "-" * 70)
    print("🔧 GENERATING PACK")
    print("-" * 70)

    try:
        req = GenerateRequest(
            brief=brief,
            package_preset="launch_gtm_pack",
            wow_package_key="launch_gtm_pack",
            wow_enabled=True,
            include_agency_grade=False,
            skip_benchmark_enforcement=True,
        )
        output = await aicmo_generate(req)
        full_markdown = output.wow_markdown or output.full_report

        if not full_markdown:
            print("❌ No output generated!")
            return False

        print(f"✓ Generated {len(full_markdown):,} characters of markdown")

    except Exception as e:
        print(f"❌ GENERATION FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Step 3: Parse sections
    print("\n" + "-" * 70)
    print("📝 PARSING SECTIONS")
    print("-" * 70)

    try:
        sections = parse_wow_markdown_to_sections(full_markdown)
        print(f"✓ Parsed {len(sections)} sections from markdown")

        for sec in sections[:5]:
            print(f"  - {sec['id']}: {len(sec['content']):,} chars")
        if len(sections) > 5:
            print(f"  ... and {len(sections) - 5} more sections")

    except Exception as e:
        print(f"❌ PARSING FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Step 4: Validate sections
    print("\n" + "-" * 70)
    print("✅ VALIDATION RESULTS")
    print("-" * 70)

    try:
        result = validate_report_sections(pack_key="launch_gtm_pack", sections=sections)

        print(f"\nStatus: {result.status}")
        print(f"Sections Validated: {len(result.section_results)}")

        error_count = 0
        warning_count = 0

        for section_result in result.section_results:
            errors = [issue for issue in section_result.issues if issue.severity == "error"]
            warnings = [issue for issue in section_result.issues if issue.severity == "warning"]

            error_count += len(errors)
            warning_count += len(warnings)

            if errors or warnings:
                print(f"\n[{section_result.section_id}]")
                print(f"  Status: {section_result.status}")
                if errors:
                    print(f"  ❌ ERRORS ({len(errors)}):")
                    for issue in errors:
                        print(f"     - {issue.code}: {issue.message}")
                if warnings:
                    print(f"  ⚠️  WARNINGS ({len(warnings)}):")
                    for issue in warnings:
                        print(f"     - {issue.code}: {issue.message}")

        # Summary
        print("\n" + "=" * 70)
        print("FINAL VERDICT")
        print("=" * 70)
        print(f"Status: {result.status}")
        print(f"Errors: {error_count}")
        print(f"Warnings: {warning_count}")

        if error_count == 0:
            print("\n✅ LAUNCH_GTM_PACK PASS")
            print("All sections meet quality standards.")
            return True
        else:
            print("\n❌ LAUNCH_GTM_PACK FAIL")
            print(f"{error_count} errors must be fixed before client delivery.")
            return False

    except Exception as e:
        print(f"❌ VALIDATION FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
