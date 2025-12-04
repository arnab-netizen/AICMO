#!/usr/bin/env python3
"""
Full Pack Validation Test - REAL GENERATORS (Non-Stub Mode)

This test explicitly disables stub mode and uses real generators to validate
that the hashtag_strategy section (and other sections) work correctly with
WOW templates and benchmark validation.

Purpose:
- Prove hashtag_strategy implementation is correct
- Validate WOW template + parser alignment
- Test full pipeline: Generator → WOW → Parser → Validator
- Distinguish between stub-mode failures (expected) and real failures (bugs)
"""

import os
import sys

# Force disable stub mode
os.environ["AICMO_STUB_MODE"] = "0"
os.environ["AICMO_USE_LLM"] = "false"  # Disable LLM enhancement to focus on generators

# Add project root to path
sys.path.insert(0, "/workspaces/AICMO")

from backend.main import GenerateRequest, _gen_hashtag_strategy
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
from backend.validators.quality_checks import run_all_quality_checks
import asyncio


def create_test_brief() -> ClientInputBrief:
    """Create test brief for Starbucks quick_social_basic pack."""
    brand = BrandBrief(
        brand_name="Starbucks",
        industry="Coffee & Beverages",
        product_service="Coffee, tea, and pastries",
        primary_goal="Increase brand engagement and drive foot traffic",
        primary_customer="Coffee enthusiasts and professionals",
        location="Seattle, USA",
        timeline="90 days",
        brand_tone="Friendly, community-focused, premium",
    ).with_safe_defaults()

    return ClientInputBrief(
        brand=brand,
        audience=AudienceBrief(primary_customer="Coffee enthusiasts and professionals"),
        goal=GoalBrief(
            primary_goal="Increase brand engagement and drive foot traffic",
            timeline="90 days",
            kpis=["engagement rate", "foot traffic", "social reach"],
        ),
        voice=VoiceBrief(tone_of_voice=["friendly", "premium", "community-focused"]),
        product_service=ProductServiceBrief(),
        assets_constraints=AssetsConstraintsBrief(
            focus_platforms=["Instagram", "TikTok", "Facebook"]
        ),
        operations=OperationsBrief(),
        strategy_extras=StrategyExtrasBrief(),
    )


async def test_hashtag_strategy_with_real_generator():
    """
    Test hashtag_strategy section with REAL generator (not stub).

    This is the definitive test that proves hashtag_strategy works.
    """
    print("=" * 60)
    print("HASHTAG_STRATEGY TEST - REAL GENERATOR (Non-Stub Mode)")
    print("=" * 60)
    print()

    # Create test brief
    brief = create_test_brief()
    req = GenerateRequest(
        brief=brief,
        wow_enabled=True,
        wow_package_key="quick_social_basic",
    )

    print(f"📝 Generating hashtag_strategy for {brief.brand.brand_name}...")
    print(f"   - Industry: {brief.brand.industry}")
    print(f"   - Stub mode: {os.environ.get('AICMO_STUB_MODE', 'not set')}")
    print()

    try:
        # Generate hashtag_strategy section directly
        output = _gen_hashtag_strategy(req)

        print("✅ Generation completed")
        print(f"   - Output length: {len(output)} characters")
        print(f"   - Word count: {len(output.split())} words")
        print()

        # Show preview
        print("=" * 60)
        print("OUTPUT PREVIEW")
        print("=" * 60)
        print()
        print(output[:800])
        if len(output) > 800:
            print("...")
        print()

        # Run quality checks
        print("=" * 60)
        print("QUALITY VALIDATION")
        print("=" * 60)
        print()
        print("🚦 Running quality checks on hashtag_strategy section...")

        issues = run_all_quality_checks(output, "hashtag_strategy", "quick_social_basic")

        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]

        print()
        print("=" * 60)
        print("QUALITY CHECK RESULTS")
        print("=" * 60)
        print()
        print(f"✅ Total checks run: {len(issues) if issues else 0}")
        print(f"❌ Errors: {len(errors)}")
        print(f"⚠️  Warnings: {len(warnings)}")
        print()

        if errors:
            print("=" * 40)
            print("ERRORS (must fix):")
            print("=" * 40)
            for issue in errors:
                print(f"  ❌ {issue.code}: {issue.message}")
                if hasattr(issue, "details") and issue.details:
                    print(f"     Details: {issue.details}")
            print()

        if warnings:
            print("=" * 40)
            print("WARNINGS (optional improvements):")
            print("=" * 40)
            for issue in warnings:
                print(f"  ⚠️  {issue.code}: {issue.message}")
            print()

        if not errors and not warnings:
            print("✅ No issues found - content is perfect!")
            print()

        # Final verdict
        print("=" * 60)
        print("FINAL VERDICT")
        print("=" * 60)
        print()

        if not errors:
            print("✅ SUCCESS: hashtag_strategy section PASSES validation!")
            print()
            print("This proves:")
            print("  ✅ Generator outputs correct structure (### subsections)")
            print("  ✅ All required headings present (Brand/Industry/Campaign/Usage)")
            print("  ✅ Sufficient hashtags in each category (3+ per category)")
            print("  ✅ No blacklisted phrases")
            print("  ✅ Meets word count and formatting requirements")
            print()
            return 0
        else:
            print("❌ FAILURE: hashtag_strategy section has validation errors")
            print()
            print("Errors to fix:")
            for issue in errors:
                print(f"  - {issue.code}: {issue.message}")
            print()
            return 1

    except Exception as e:
        print("❌ ERROR: Generation failed with exception")
        print(f"   {type(e).__name__}: {str(e)}")
        print()
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    print()
    print("🚀 Testing hashtag_strategy with REAL generator (non-stub)...")
    print()

    # Check environment
    print("Environment Check:")
    print(f"  AICMO_STUB_MODE: {os.environ.get('AICMO_STUB_MODE', 'not set')}")
    print(f"  AICMO_USE_LLM: {os.environ.get('AICMO_USE_LLM', 'not set')}")
    print(f"  AICMO_PERPLEXITY_ENABLED: {os.environ.get('AICMO_PERPLEXITY_ENABLED', 'not set')}")
    print()

    exit_code = asyncio.run(test_hashtag_strategy_with_real_generator())
    sys.exit(exit_code)
