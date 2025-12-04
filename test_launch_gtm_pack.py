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

from backend.main import GenerateRequest
from aicmo.io.client_reports import BrandBrief, GoalBrief
from backend.utils.wow_markdown_parser import parse_wow_markdown_to_sections
from backend.validators.report_gate import validate_report_sections


def create_test_brief() -> GenerateRequest:
    """Create realistic brief for launch_gtm_pack testing."""
    brand = BrandBrief(
        brand_name="LaunchBox",
        industry="SaaS - B2B Software",
        geography="North America",
        website_url="https://launchbox.io",
        value_proposition="AI-powered product launch management platform that helps product teams execute flawless launches with automated workflows and market intelligence",
        target_persona_label="Product Marketing Managers, Product Managers, and Growth Leads at B2B SaaS companies",
        voice_notes="Professional, innovative, data-driven, results-oriented. Speak directly to product leaders who value execution excellence.",
    )

    goal = GoalBrief(
        primary_goal="Launch new AI Launch Assistant feature to existing customer base and attract 50K new sign-ups in 90 days",
        timeline="90 days (Q1 2025)",
        kpis=[
            "50,000 new sign-ups",
            "1,000 paid conversions ($99/month tier)",
            "4.5+ app store rating",
            "60% feature activation rate",
            "100+ press mentions and reviews",
        ],
        secondary_goals=[
            "Build pre-launch waitlist of 10,000 qualified leads",
            "Achieve Product Hunt #1 Product of the Day",
            "Generate $100K MRR from new feature within 90 days",
            "Establish thought leadership via 20+ podcast/webinar appearances",
        ],
        success_criteria="Successfully launch AI Launch Assistant with strong market adoption, media coverage, and revenue impact. Establish LaunchBox as the category leader in AI-powered launch management.",
    )

    return GenerateRequest(
        brief=type("Brief", (), {"brand": brand, "goal": goal})(),
        wow_enabled=True,
        wow_package_key="launch_gtm_pack",
    )


def test_all_sections():
    """Test all 13 launch_gtm_pack sections for validation compliance."""
    req = create_test_brief()

    # Use the full pack generation pipeline (like strategy_campaign_standard test)
    from backend.main import aicmo_generate

    print("\n" + "=" * 70)
    print("LAUNCH_GTM_PACK VALIDATION TEST")
    print("=" * 70)
    print(f"Brand: {req.brief.brand.brand_name}")
    print(f"Goal: {req.brief.goal.primary_goal}")
    print("Pack: launch_gtm_pack")

    # Generate full pack
    print("\n" + "-" * 70)
    print("GENERATING PACK")
    print("-" * 70)

    try:
        output = aicmo_generate(req)
        full_markdown = output.wow_markdown or output.full_report

        if not full_markdown:
            print("❌ No output generated!")
            return False

        print(f"✓ Generated {len(full_markdown)} characters of markdown")

    except Exception as e:
        print(f"❌ GENERATION FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Parse sections
    print("\n" + "-" * 70)
    print("PARSING SECTIONS")
    print("-" * 70)

    sections = parse_wow_markdown_to_sections(full_markdown)
    print(f"Parsed {len(sections)} sections from markdown")

    for sec in sections:
        print(f"  - {sec.section_id}: {len(sec.content)} chars")

    # Validate sections
    print("\n" + "-" * 70)
    print("VALIDATION RESULTS")
    print("-" * 70)

    result = validate_report_sections(
        pack_key="launch_gtm_pack", sections=sections, brief=req.brief
    )

    print(f"\n✅ Overall Status: {result.status}")
    print(f"📊 Sections Validated: {len(result.section_results)}")

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


if __name__ == "__main__":
    success = test_all_sections()
    sys.exit(0 if success else 1)
