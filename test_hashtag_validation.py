#!/usr/bin/env python3
"""
Test script to validate hashtag_strategy section with benchmark gate.

This script:
1. Generates a Quick Social report for a test brand
2. Parses the WOW markdown output
3. Runs validate_report_sections() on hashtag_strategy
4. Reports PASS/FAIL status
"""

from pathlib import Path
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
from backend.main import GenerateRequest
from backend.services.brand_research import get_brand_research


def create_test_brief():
    """Create a test brief for Starbucks."""
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

    # Attach Perplexity research data
    print("🔍 Fetching Perplexity research for Starbucks...")
    research = get_brand_research(
        brand_name="Starbucks",
        industry="Coffee & Beverages",
        location="Seattle, USA",
        enabled=True,
    )

    if research:
        print("✅ Got research data:")
        print(
            f"   - Brand hashtags: {research.keyword_hashtags[:5] if research.keyword_hashtags else 'None'}"
        )
        print(
            f"   - Industry hashtags: {research.industry_hashtags[:5] if research.industry_hashtags else 'None'}"
        )
        print(
            f"   - Campaign hashtags: {research.campaign_hashtags[:5] if research.campaign_hashtags else 'None'}"
        )
        brand.research = research
    else:
        print("⚠️  No Perplexity data available, will use fallbacks")

    brief = ClientInputBrief(
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

    return brief


def generate_hashtag_section():
    """Generate hashtag_strategy section."""
    from backend.main import _gen_hashtag_strategy

    print("\n📝 Generating hashtag_strategy section...")
    brief = create_test_brief()
    req = GenerateRequest(brief=brief, wow_enabled=True, wow_package_key="quick_social_basic")

    output = _gen_hashtag_strategy(req)

    print(f"\n✅ Generated {len(output)} characters of content")
    print("\n--- OUTPUT PREVIEW ---")
    print(output[:500] + "..." if len(output) > 500 else output)
    print("--- END PREVIEW ---\n")

    return output


def validate_with_benchmark_gate(section_content: str):
    """Validate hashtag_strategy section content directly."""
    from backend.validators.quality_checks import run_all_quality_checks

    print("🚦 Running quality checks on hashtag_strategy section...")

    # Run quality checks directly on the content
    issues = run_all_quality_checks(section_content, section_id="hashtag_strategy")

    # Separate errors from warnings
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]

    print(f"\n{'='*60}")
    print("QUALITY CHECK RESULTS")
    print(f"{'='*60}")
    print(f"\n✅ Total checks run: {len(issues)}")
    print(f"❌ Errors: {len(errors)}")
    print(f"⚠️  Warnings: {len(warnings)}")

    if errors:
        print(f"\n{'='*40}")
        print("ERRORS (must fix):")
        print(f"{'='*40}")
        for issue in errors:
            print(f"  ❌ {issue.code}: {issue.message}")
            if issue.details:
                print(f"     Details: {issue.details}")

    if warnings:
        print(f"\n{'='*40}")
        print("WARNINGS (optional improvements):")
        print(f"{'='*40}")
        for issue in warnings:
            print(f"  ⚠️  {issue.code}: {issue.message}")

    if not errors and not warnings:
        print("\n✅ No issues found - content is perfect!")

    # Return True if no errors (warnings are acceptable)
    return len(errors) == 0


def main():
    """Main test execution."""
    print("=" * 60)
    print("HASHTAG STRATEGY BENCHMARK VALIDATION TEST")
    print("=" * 60)

    try:
        # Generate section
        output = generate_hashtag_section()

        # Save to file for inspection
        output_path = Path("tmp/hashtag_test_output.md")
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text(output)
        print(f"💾 Saved output to: {output_path}")

        # Validate content directly (not wrapped in WOW structure)
        passed = validate_with_benchmark_gate(output)

        print("\n" + "=" * 60)
        if passed:
            print("✅ SUCCESS: hashtag_strategy PASSES all quality checks!")
        else:
            print("❌ FAILURE: hashtag_strategy has validation errors")
        print("=" * 60)

        return 0 if passed else 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
