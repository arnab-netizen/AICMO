#!/usr/bin/env python3
"""
Smoke test runner for AICMO pack generation.

Quick pre-flight check to verify all packs can generate without errors.
Runs a subset of pack benchmarks through the internal handler.

Usage:
    # Without LLM (uses stubs):
    python scripts/smoke_run_all_packs.py
    
    # With LLM configured:
    export OPENAI_API_KEY=sk-...
    python scripts/smoke_run_all_packs.py
    
    # Production mode (no stubs):
    export OPENAI_API_KEY=sk-...
    export AICMO_ALLOW_STUBS=false
    python scripts/smoke_run_all_packs.py
"""

import sys
import asyncio
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.main import api_aicmo_generate_report
from backend.utils.config import has_llm_configured, allow_stubs_in_production


# Subset of packs to test (covers different tiers/types)
SMOKE_TEST_PACKS = [
    {
        "pack_key": "quick_social_basic",
        "benchmark": "pack_quick_social_basic_d2c.json",
        "name": "Quick Social (Basic)",
    },
    {
        "pack_key": "strategy_campaign_standard",
        "benchmark": "agency_report_automotive_luxotica.json",
        "name": "Strategy+Campaign (Standard)",
    },
    {
        "pack_key": "full_funnel_growth_suite",
        "benchmark": "pack_full_funnel_growth_suite_saas.json",
        "name": "Full-Funnel Growth Suite",
    },
]


def load_benchmark(benchmark_file: str) -> dict:
    """Load benchmark JSON file."""
    benchmarks_dir = Path(__file__).resolve().parent.parent / "learning" / "benchmarks"
    path = benchmarks_dir / benchmark_file

    if not path.exists():
        print(f"❌ Benchmark not found: {path}")
        return {}

    with path.open("r") as f:
        return json.load(f)


def build_payload(pack_key: str, benchmark: dict) -> dict:
    """Build API payload from benchmark."""
    brief = benchmark.get("brief", {})

    return {
        "pack_key": pack_key,
        "stage": "draft",
        "client_brief": {
            "brand_name": brief.get("brand_name", "Test Brand"),
            "industry": brief.get("industry", "Test Industry"),
            "product_service": brief.get("product_service", "Test Product"),
            "primary_goal": brief.get("primary_goal", "Test Goal"),
            "geography": brief.get("geography", "United States"),
            "target_audience": brief.get("target_audience", "Test Audience"),
        },
        "services": {
            "marketing_plan": True,
            "campaign_blueprint": True,
            "social_calendar": True,
        },
    }


async def run_smoke_test(pack_info: dict) -> dict:
    """Run smoke test for a single pack."""
    pack_key = pack_info["pack_key"]
    benchmark_file = pack_info["benchmark"]
    name = pack_info["name"]

    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"Pack Key: {pack_key}")
    print(f"{'='*70}")

    # Load benchmark
    benchmark = load_benchmark(benchmark_file)
    if not benchmark:
        return {
            "pack_key": pack_key,
            "name": name,
            "success": False,
            "error": "Benchmark file not found",
        }

    # Build payload
    payload = build_payload(pack_key, benchmark)

    # Call API handler
    try:
        result = await api_aicmo_generate_report(payload)

        success = result.get("success", False)
        stub_used = result.get("stub_used", True)
        markdown = result.get("report_markdown", "")
        error_type = result.get("error_type")
        error_message = result.get("error_message", "")

        return {
            "pack_key": pack_key,
            "name": name,
            "success": success,
            "stub_used": stub_used,
            "markdown_length": len(markdown),
            "error_type": error_type,
            "error_message": error_message[:100] if error_message else None,
        }
    except Exception as e:
        return {
            "pack_key": pack_key,
            "name": name,
            "success": False,
            "error": f"{type(e).__name__}: {str(e)[:100]}",
        }


async def main():
    """Run smoke tests for all packs."""
    print("\n" + "=" * 70)
    print(" AICMO Pack Smoke Test Runner")
    print("=" * 70)

    # Check environment
    llm_configured = has_llm_configured()
    allow_stubs = allow_stubs_in_production()

    print("\n📋 Environment:")
    print(f"   LLM Configured: {'✅ Yes' if llm_configured else '❌ No'}")
    print(f"   Stubs Allowed: {'✅ Yes' if allow_stubs else '❌ No'}")

    if not llm_configured and not allow_stubs:
        print("\n⚠️  WARNING: No LLM configured and stubs disabled!")
        print("   All packs will fail with 'llm_unavailable' error.")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY to test with LLM.")
        print("   Or set AICMO_ALLOW_STUBS=true to allow stub content.")

    # Run tests
    results = []
    for pack_info in SMOKE_TEST_PACKS:
        result = await run_smoke_test(pack_info)
        results.append(result)

        # Print immediate result
        if result["success"]:
            print("✅ SUCCESS")
            print(f"   Stub Used: {'Yes' if result.get('stub_used') else 'No'}")
            print(f"   Length: {result.get('markdown_length', 0)} chars")
        else:
            print("❌ FAILED")
            if "error" in result:
                print(f"   Error: {result['error']}")
            else:
                print(f"   Error Type: {result.get('error_type', 'unknown')}")
                if result.get("error_message"):
                    print(f"   Message: {result['error_message']}")

    # Summary
    print(f"\n{'='*70}")
    print(" Summary")
    print("=" * 70)

    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed

    print(f"\n📊 Results: {passed}/{len(results)} passed")

    if failed > 0:
        print("\n❌ Failed Packs:")
        for result in results:
            if not result["success"]:
                print(f"   - {result['name']} ({result['pack_key']})")
                if "error" in result:
                    print(f"     {result['error']}")
                elif result.get("error_type"):
                    print(f"     {result['error_type']}: {result.get('error_message', '')[:80]}")

    if passed == len(results):
        print(f"\n✅ All {passed} packs passed smoke test!")
        return 0
    else:
        print(f"\n⚠️  {failed} pack(s) failed. Review errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
