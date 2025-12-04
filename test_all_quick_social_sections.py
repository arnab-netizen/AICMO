#!/usr/bin/env python3
"""
Comprehensive test for ALL 8 Quick Social Pack sections.

Tests all sections with real generators (non-stub mode) to ensure:
- All sections generate valid content
- All sections pass quality validation
- All sections meet benchmark requirements
- Quick Social Pack is client-ready and agency-grade

The 8 sections tested:
1. Brand & Context Snapshot (overview)
2. Messaging Framework (messaging_framework)
3. 30-Day Content Calendar (detailed_30_day_calendar)
4. Content Buckets & Themes (content_buckets)
5. Hashtag Strategy (hashtag_strategy)
6. KPIs & Lightweight Measurement Plan (kpi_plan_light)
7. Execution Roadmap (execution_roadmap)
8. Final Summary & Next Steps (final_summary)
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
from backend.validators.quality_checks import run_all_quality_checks


# Import all generator functions
from backend.main import (
    _gen_overview,
    _gen_messaging_framework,
    _gen_quick_social_30_day_calendar,
    _gen_content_buckets,
    _gen_hashtag_strategy,
    _gen_kpi_plan_light,
    _gen_execution_roadmap,
    _gen_final_summary,
)


def create_test_brief() -> ClientInputBrief:
    """Create test brief for Starbucks in coffeehouse industry."""
    brand = BrandBrief(
        brand_name="Starbucks",
        industry="Coffee & Beverages",
        product_service="Premium coffee and café experience",
        primary_goal="Boost daily in-store footfall & increase social media engagement",
        primary_customer="coffee enthusiasts and urban professionals",
        location="Seattle, WA, USA",
        timeline="30 days",
        brand_tone="welcoming, premium, community-focused",
    ).with_safe_defaults()

    brief = ClientInputBrief(
        brand=brand,
        audience=AudienceBrief(primary_customer="coffee enthusiasts and professionals"),
        goal=GoalBrief(primary_goal="Boost daily in-store footfall"),
        voice=VoiceBrief(brand_tone="welcoming"),
        product_service=ProductServiceBrief(product_service="Coffee and café"),
        assets_constraints=AssetsConstraintsBrief(),
        operations=OperationsBrief(),
        strategy_extras=StrategyExtrasBrief(),
    )

    return brief


async def test_single_section(section_id: str, section_name: str, generator_func) -> dict:
    """Test a single Quick Social Pack section."""
    print(f"\n{'='*80}")
    print(f"Testing Section: {section_name}")
    print(f"Section ID: {section_id}")
    print(f"{'='*80}\n")

    brief = create_test_brief()

    # Generate section directly
    try:
        print(f"📝 Generating {section_id}...")
        req = GenerateRequest(
            brief=brief,
            wow_package_key="quick_social_basic",
        )

        # Call the generator function directly
        section_content = generator_func(req)

        if not section_content:
            return {
                "section_id": section_id,
                "section_name": section_name,
                "status": "FAIL",
                "error": "Generator returned empty content",
                "output": None,
            }
        word_count = len(section_content.split())
        char_count = len(section_content)

        print("✅ Generation completed")
        print(f"   - Output length: {char_count} characters")
        print(f"   - Word count: {word_count} words")

        # Show preview
        print(f"\n{'-'*80}")
        print("OUTPUT PREVIEW")
        print(f"{'-'*80}\n")
        preview = section_content[:500] + "..." if len(section_content) > 500 else section_content
        print(preview)

        # Run quality checks
        print(f"\n{'-'*80}")
        print("QUALITY VALIDATION")
        print(f"{'-'*80}\n")

        print(f"🚦 Running quality checks on {section_id}...")
        quality_result = run_all_quality_checks(
            section_content, brief.brand, section_type=section_id
        )

        print(f"\n{'-'*80}")
        print("QUALITY CHECK RESULTS")
        print(f"{'-'*80}\n")

        total_checks = len(quality_result.get("checks_run", []))
        errors = quality_result.get("errors", [])
        warnings = quality_result.get("warnings", [])

        print(f"✅ Total checks run: {total_checks}")
        print(f"❌ Errors: {len(errors)}")
        print(f"⚠️  Warnings: {len(warnings)}")

        if errors:
            print("\n❌ ERRORS FOUND:")
            for error in errors:
                print(f"   - {error}")

        if warnings:
            print("\n⚠️  WARNINGS:")
            for warning in warnings:
                print(f"   - {warning}")

        if not errors and not warnings:
            print("\n✅ No issues found - content is perfect!")

        # Determine pass/fail
        status = "PASS" if len(errors) == 0 else "FAIL"

        return {
            "section_id": section_id,
            "section_name": section_name,
            "status": status,
            "word_count": word_count,
            "char_count": char_count,
            "errors": errors,
            "warnings": warnings,
            "output": section_content,
        }

    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback

        traceback.print_exc()
        return {
            "section_id": section_id,
            "section_name": section_name,
            "status": "ERROR",
            "error": str(e),
            "output": None,
        }


async def test_all_quick_social_sections():
    """Test all 8 Quick Social Pack sections."""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE QUICK SOCIAL PACK TEST")
    print("Testing ALL 8 Sections with Real Generators")
    print("=" * 80)

    # Check environment
    print("\nEnvironment Check:")
    print(f"  AICMO_STUB_MODE: {os.getenv('AICMO_STUB_MODE', 'not set')}")
    print(f"  AICMO_USE_LLM: {os.getenv('AICMO_USE_LLM', 'not set')}")
    print(f"  AICMO_PERPLEXITY_ENABLED: {os.getenv('AICMO_PERPLEXITY_ENABLED', 'not set')}")

    # Define all 8 sections with their generator functions
    sections_to_test = [
        ("overview", "Brand & Context Snapshot", _gen_overview),
        ("messaging_framework", "Messaging Framework", _gen_messaging_framework),
        ("detailed_30_day_calendar", "30-Day Content Calendar", _gen_quick_social_30_day_calendar),
        ("content_buckets", "Content Buckets & Themes", _gen_content_buckets),
        ("hashtag_strategy", "Hashtag Strategy", _gen_hashtag_strategy),
        ("kpi_plan_light", "KPIs & Lightweight Measurement Plan", _gen_kpi_plan_light),
        ("execution_roadmap", "Execution Roadmap", _gen_execution_roadmap),
        ("final_summary", "Final Summary & Next Steps", _gen_final_summary),
    ]

    results = []

    for section_id, section_name, generator_func in sections_to_test:
        result = await test_single_section(section_id, section_name, generator_func)
        results.append(result)

    # Summary report
    print("\n" + "=" * 80)
    print("FINAL SUMMARY REPORT")
    print("=" * 80 + "\n")

    passed = [r for r in results if r["status"] == "PASS"]
    failed = [r for r in results if r["status"] == "FAIL"]
    errors = [r for r in results if r["status"] == "ERROR"]

    print("📊 Test Results:")
    print(f"   ✅ Passed: {len(passed)}/{len(results)}")
    print(f"   ❌ Failed: {len(failed)}/{len(results)}")
    print(f"   💥 Errors: {len(errors)}/{len(results)}")

    print("\n📋 Section-by-Section Results:\n")

    for result in results:
        status_icon = (
            "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "💥"
        )
        print(f"{status_icon} {result['section_name']}")
        print(f"   Section ID: {result['section_id']}")
        print(f"   Status: {result['status']}")

        if result.get("word_count"):
            print(f"   Word Count: {result['word_count']}")

        if result.get("errors"):
            print(f"   Errors: {len(result['errors'])}")
            for error in result["errors"][:3]:  # Show first 3 errors
                print(f"      - {error}")

        if result.get("error"):
            print(f"   Error: {result['error']}")

        print()

    # Final verdict
    print("=" * 80)
    print("FINAL VERDICT")
    print("=" * 80 + "\n")

    if len(passed) == len(results):
        print("🎉 SUCCESS! ALL 8 SECTIONS PASS VALIDATION!")
        print("\nThis Quick Social Pack is:")
        print("  ✅ Client-ready")
        print("  ✅ Agency-grade quality")
        print("  ✅ Brand-agnostic (uses dynamic data)")
        print("  ✅ Grammatically correct")
        print("  ✅ No generic marketing jargon")
        print("  ✅ Suitable for PDF export to paying clients")
        return True
    else:
        print(f"❌ ISSUES FOUND: {len(failed) + len(errors)} sections need attention\n")

        if failed:
            print("Failed sections (validation errors):")
            for r in failed:
                print(f"  - {r['section_name']}: {len(r.get('errors', []))} errors")

        if errors:
            print("\nError sections (generation failures):")
            for r in errors:
                print(f"  - {r['section_name']}: {r.get('error', 'Unknown error')}")

        print("\n⚠️  Quick Social Pack needs fixes before client delivery.")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_all_quick_social_sections())
    sys.exit(0 if success else 1)
