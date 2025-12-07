#!/usr/bin/env python3
"""
Live LLM verification CLI tool.

Tests AICMO with real packs to verify:
1. Real LLM usage (no stubs)
2. Quality checks passing
3. Proper content generation

Exit codes:
- 0: All tests passed (success=True, stub_used=False, quality_passed=True)
- 1: Any test failed or used stubs in production
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.client.aicmo_api_client import call_generate_report
from backend.utils.config import is_production_llm_ready


def load_benchmark(benchmark_file: str) -> Dict[str, Any]:
    """Load a benchmark JSON file."""
    benchmark_path = Path(__file__).parent.parent / "learning" / "benchmarks" / benchmark_file

    if not benchmark_path.exists():
        print(f"❌ Benchmark file not found: {benchmark_path}")
        sys.exit(1)

    with open(benchmark_path, "r") as f:
        return json.load(f)


def build_payload_from_benchmark(benchmark: Dict[str, Any]) -> Dict[str, Any]:
    """Convert benchmark JSON to API payload format."""
    brief = benchmark.get("brief", {})

    return {
        "pack_key": benchmark.get("pack_key"),
        "client_brief": brief,  # Pass the brief dict directly
        "stage": "strategy",
        "services": {
            "branding": True,
            "paid_media": True,
            "social_content": True,
            "email_marketing": True,
            "seo": True,
            "influencer": False,
            "crm": False,
            "analytics": True,
        },
        "persona_tolerance": "strict",
        "model_preference": "auto",
    }


def run_test(benchmark_file: str) -> Dict[str, Any]:
    """
    Run a single test with a benchmark file.

    Returns:
        Dict with test results including success, stub_used, quality_passed
    """
    print(f"\n{'='*80}")
    print(f"Testing: {benchmark_file}")
    print(f"{'='*80}")

    # Load benchmark
    benchmark = load_benchmark(benchmark_file)
    pack_key = benchmark.get("pack_key")
    brand_name = benchmark.get("brand_name")

    print(f"📦 Pack: {pack_key}")
    print(f"🏢 Brand: {brand_name}")

    # Build payload
    payload = build_payload_from_benchmark(benchmark)

    # Call API
    print("🔄 Generating report...")
    response = call_generate_report(payload)

    # Extract results
    success = response.get("success", False)
    stub_used = response.get("stub_used", True)
    quality_passed = response.get("quality_passed", False)
    error_type = response.get("error_type")
    error_message = response.get("error_message")
    markdown = response.get("markdown", "")

    # Print results
    print("\n📊 Results:")
    print(f"  ✓ Success: {success}")
    print(f"  ✓ Stub Used: {stub_used}")
    print(f"  ✓ Quality Passed: {quality_passed}")

    if error_type:
        print(f"  ❌ Error Type: {error_type}")
        print(f"  ❌ Error Message: {error_message}")

    if markdown:
        print(f"  📝 Markdown Length: {len(markdown)} chars")
        print("\n📄 Preview (first 300 chars):")
        print(f"  {markdown[:300]}...")

    return {
        "benchmark_file": benchmark_file,
        "pack_key": pack_key,
        "brand_name": brand_name,
        "success": success,
        "stub_used": stub_used,
        "quality_passed": quality_passed,
        "error_type": error_type,
        "markdown_length": len(markdown),
    }


def main():
    """Run live LLM verification tests."""
    print("🚀 AICMO Live LLM Verification")
    print("=" * 80)

    # Check LLM readiness
    llm_ready = is_production_llm_ready()
    print(f"🔧 LLM Ready: {llm_ready}")

    if not llm_ready:
        print("\n⚠️  WARNING: No production LLM keys detected!")
        print("   This test will likely show stub_used=True (expected in dev)")
        print("   Set OPENAI_API_KEY or PERPLEXITY_API_KEY to test real LLMs")

    # Test cases - use a few representative benchmarks
    test_cases = [
        "pack_quick_social_basic_d2c.json",
        "pack_strategy_campaign_basic_fitness.json",
    ]

    results: List[Dict[str, Any]] = []
    all_passed = True

    for benchmark_file in test_cases:
        try:
            result = run_test(benchmark_file)
            results.append(result)

            # Check if this test passed production criteria
            if llm_ready:
                # In production mode, we require:
                # - success=True
                # - stub_used=False
                # - quality_passed=True
                if not result["success"]:
                    print("  ❌ FAIL: success=False")
                    all_passed = False
                elif result["stub_used"]:
                    print("  ❌ FAIL: stub_used=True (stubs forbidden in production)")
                    all_passed = False
                elif not result["quality_passed"]:
                    print("  ❌ FAIL: quality_passed=False")
                    all_passed = False
                else:
                    print("  ✅ PASS: Real LLM, quality passed")
            else:
                # In dev mode, just check success
                if result["success"]:
                    print(
                        f"  ✅ PASS: Generation succeeded (stub_used={result['stub_used']} OK in dev)"
                    )
                else:
                    print("  ❌ FAIL: Generation failed")
                    all_passed = False

        except Exception as exc:
            print(f"  ❌ ERROR: {exc}")
            results.append(
                {
                    "benchmark_file": benchmark_file,
                    "error": str(exc),
                }
            )
            all_passed = False

    # Summary
    print(f"\n{'='*80}")
    print("📈 Summary")
    print(f"{'='*80}")
    print(f"Total tests: {len(test_cases)}")
    print(f"Results: {len(results)}")

    passed_count = sum(
        1 for r in results if r.get("success") and (not llm_ready or not r.get("stub_used"))
    )
    print(f"✅ Passed: {passed_count}/{len(test_cases)}")

    if llm_ready:
        stub_count = sum(1 for r in results if r.get("stub_used"))
        if stub_count > 0:
            print(f"⚠️  Stubs used: {stub_count} (FORBIDDEN in production)")

    # Exit code
    if all_passed:
        print("\n✅ All tests PASSED")
        sys.exit(0)
    else:
        print("\n❌ Some tests FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
