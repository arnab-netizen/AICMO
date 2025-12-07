"""
Comprehensive Pack Simulation Test Suite

Tests ALL AICMO packs against real benchmarks with hard verification.
No assumptions - only real execution and evidence-based pass/fail.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import json
import asyncio
from typing import Any, Dict
from dataclasses import dataclass, field
from difflib import unified_diff, SequenceMatcher

import pytest

from backend.main import api_aicmo_generate_report


BENCHMARKS_DIR = Path(__file__).resolve().parent.parent.parent / "learning" / "benchmarks"
GOLDENS_DIR = Path(__file__).resolve().parent.parent.parent / "learning" / "goldens"

# Detect if LLM is configured
LLM_CONFIGURED = bool(os.getenv("OPENAI_API_KEY")) or bool(os.getenv("ANTHROPIC_API_KEY"))

# All benchmark files for parametrization
ALL_BENCHMARK_FILES = [
    "pack_quick_social_basic_d2c.json",
    "pack_strategy_campaign_basic_fitness.json",
    "agency_report_automotive_luxotica.json",
    "pack_strategy_campaign_premium_edtech.json",
    "pack_strategy_campaign_enterprise_financial.json",
    "pack_full_funnel_growth_suite_saas.json",
    "pack_launch_gtm_consumer_electronics.json",
    "pack_brand_turnaround_furniture.json",
    "pack_retention_crm_coffee.json",
    "pack_performance_audit_activegear.json",
]


@dataclass
class PackSimulationResult:
    """Hard evidence of pack simulation outcome."""

    pack_key: str
    success: bool
    reason: str
    required_terms_missing: list[str] = field(default_factory=list)
    forbidden_terms_found: list[str] = field(default_factory=list)
    brand_mentions: int = 0
    markdown_length: int = 0
    markdown_excerpt: str = ""
    pdf_rendered: bool = False
    quality_gate_passed: bool = False
    error_message: str = ""
    stub_used: bool = True  # Track whether stub content was used
    golden_diff: str | None = None  # Text diff vs golden response
    golden_similarity: float | None = None  # 0.0-1.0 similarity score


def load_pack_benchmark(benchmark_file: str) -> Dict[str, Any]:
    """Load a pack benchmark JSON."""
    path = BENCHMARKS_DIR / benchmark_file
    if not path.exists():
        raise FileNotFoundError(f"Benchmark not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_brief_payload(benchmark: Dict[str, Any]) -> Dict[str, Any]:
    """Build API payload from benchmark brief."""
    brief_data = benchmark.get("brief", {})

    return {
        "stage": "final",
        "client_brief": {
            "brand_name": brief_data.get("brand_name", ""),
            "industry": brief_data.get("industry", ""),
            "product_service": brief_data.get("product_service", ""),
            "primary_goal": brief_data.get("primary_goal", ""),
            "geography": brief_data.get("geography", ""),
            "target_audience": brief_data.get("target_audience", ""),
            "voice": brief_data.get("voice", ""),
            "positioning_summary": brief_data.get("positioning_summary", ""),
            "raw_brief_text": (
                f"{brief_data.get('brand_name', 'Brand')} in {brief_data.get('industry', 'industry')}. "
                f"Goal: {brief_data.get('primary_goal', 'growth')}. "
                f"Audience: {brief_data.get('target_audience', 'target market')}."
            ),
        },
        "services": {
            "include_agency_grade": False,
            "marketing_plan": True,
            "campaign_blueprint": True,
            "social_calendar": True,
        },
        "wow_package_preset": benchmark.get("pack_key", "quick_social_basic"),
    }


def golden_path_for_benchmark(benchmark_file: str) -> Path:
    """Map benchmark file to golden markdown file."""
    # Special case: automotive uses different naming
    if benchmark_file == "agency_report_automotive_luxotica.json":
        return GOLDENS_DIR / "strategy_campaign_standard_luxotica.md"

    # Standard case: strip "pack_" prefix and change extension
    name = benchmark_file.replace("pack_", "").replace(".json", ".md")
    return GOLDENS_DIR / name


def load_golden_markdown(benchmark_file: str) -> str | None:
    """Load golden markdown content if it exists."""
    golden_path = golden_path_for_benchmark(benchmark_file)
    if not golden_path.exists():
        return None
    return golden_path.read_text(encoding="utf-8")


def compute_golden_diff(golden: str, actual: str) -> str:
    """Compute unified diff between golden and actual output."""
    golden_lines = golden.splitlines(keepends=True)
    actual_lines = actual.splitlines(keepends=True)

    diff_lines = list(
        unified_diff(golden_lines, actual_lines, fromfile="golden", tofile="actual", lineterm="")
    )

    # Limit diff to first 50 lines to avoid massive output
    if len(diff_lines) > 50:
        diff_lines = diff_lines[:50] + ["... (diff truncated)\n"]

    return "".join(diff_lines)


def run_pack_simulation_sync(benchmark_file: str) -> PackSimulationResult:
    """Run a single pack simulation synchronously."""
    try:
        benchmark = load_pack_benchmark(benchmark_file)
        pack_key = benchmark.get("pack_key", "unknown")

        # Build payload and call real API handler
        payload = build_brief_payload(benchmark)

        # Call async API handler synchronously
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(api_aicmo_generate_report(payload))

        # Extract results
        status = result.get("status", "error")
        markdown = result.get("report_markdown", "")
        stub_used = result.get("stub_used", True)  # Extract stub flag
        markdown_lower = markdown.lower()

        if status != "success":
            return PackSimulationResult(
                pack_key=pack_key,
                success=False,
                reason=f"Generation failed: {result.get('error_message', 'Unknown error')}",
                error_message=result.get("error_message", ""),
                markdown_excerpt=markdown[:500] if markdown else "(empty)",
                stub_used=True,
            )

        # Verify required terms
        required_terms = benchmark.get("required_terms", [])
        missing_terms = [term for term in required_terms if term.lower() not in markdown_lower]

        # Verify forbidden terms
        forbidden_terms = benchmark.get("forbidden_terms", [])
        found_forbidden = [term for term in forbidden_terms if term.lower() in markdown_lower]

        # Count brand mentions
        brand_name = benchmark.get("brand_name", "")
        brand_mentions = markdown_lower.count(brand_name.lower()) if brand_name else 0
        min_brand_mentions = benchmark.get("min_brand_mentions", 3)

        # Determine success
        success = not missing_terms and not found_forbidden and brand_mentions >= min_brand_mentions

        # Build reason
        reasons = []
        if missing_terms:
            reasons.append(f"Missing required terms: {missing_terms}")
        if found_forbidden:
            reasons.append(f"Forbidden terms found: {found_forbidden}")
        if brand_mentions < min_brand_mentions:
            reasons.append(f"Insufficient brand mentions: {brand_mentions} < {min_brand_mentions}")

        reason = "; ".join(reasons) if reasons else "All checks passed"

        # Compute golden diff if LLM is configured
        golden_diff = None
        golden_similarity = None
        if not stub_used:  # Only compute diff for real LLM output
            golden_markdown = load_golden_markdown(benchmark_file)
            if golden_markdown:
                golden_diff = compute_golden_diff(golden_markdown, markdown)
                # Compute similarity ratio
                matcher = SequenceMatcher(None, golden_markdown, markdown)
                golden_similarity = matcher.ratio()

        return PackSimulationResult(
            pack_key=pack_key,
            success=success,
            reason=reason,
            required_terms_missing=missing_terms,
            forbidden_terms_found=found_forbidden,
            brand_mentions=brand_mentions,
            markdown_length=len(markdown),
            markdown_excerpt=markdown[:300],
            pdf_rendered=False,  # We'd need to check PDF bytes
            quality_gate_passed=status == "success",
            stub_used=stub_used,  # Include stub flag
            golden_diff=golden_diff,
            golden_similarity=golden_similarity,
        )

    except Exception as e:
        return PackSimulationResult(
            pack_key=benchmark.get("pack_key", "unknown"),
            success=False,
            reason=f"Exception during simulation: {str(e)}",
            error_message=str(e),
            stub_used=True,
        )


# Main parametrized test for all packs
@pytest.mark.integration
@pytest.mark.parametrize("benchmark_file", ALL_BENCHMARK_FILES)
def test_pack_meets_benchmark(benchmark_file: str):
    """
    Test that a pack meets its benchmark criteria.

    Behavior:
    - If LLM not configured: Skip test with clear message
    - If LLM configured but stub used: Fail with "stub content used"
    - If LLM configured and no stub: Validate all quality gates
    """
    # STEP 4: Honest behavior when no LLM configured
    if not LLM_CONFIGURED:
        pytest.skip(
            "LLM not configured (OPENAI_API_KEY/ANTHROPIC_API_KEY missing) – "
            "all-packs simulation cannot validate quality."
        )

    # Run the simulation
    result = run_pack_simulation_sync(benchmark_file)

    # STEP 5: Honest behavior when LLM configured - strict validation

    # Assert 1: Stub content must not be used
    assert not result.stub_used, (
        f"{result.pack_key} used stub content – cannot be considered agency-grade.\n"
        f"This indicates LLM generation failed or was bypassed.\n"
        f"Excerpt: {result.markdown_excerpt[:200]}"
    )

    # Assert 2: Required terms must all be present
    assert not result.required_terms_missing, (
        f"{result.pack_key} missing required terms: {result.required_terms_missing}\n"
        f"These domain-specific terms must appear in agency-grade output.\n"
        f"Excerpt: {result.markdown_excerpt[:200]}"
    )

    # Assert 3: Forbidden terms must be absent
    assert not result.forbidden_terms_found, (
        f"{result.pack_key} contains forbidden terms: {result.forbidden_terms_found}\n"
        f"These terms indicate wrong industry/domain context.\n"
        f"Excerpt: {result.markdown_excerpt[:200]}"
    )

    # Assert 4: Brand mentions must meet minimum threshold
    benchmark = load_pack_benchmark(benchmark_file)
    min_brand_mentions = benchmark.get("min_brand_mentions", 3)
    assert result.brand_mentions >= min_brand_mentions, (
        f"{result.pack_key} has insufficient brand mentions: "
        f"{result.brand_mentions} < {min_brand_mentions}\n"
        f"Agency-grade reports must be brand-focused.\n"
        f"Excerpt: {result.markdown_excerpt[:200]}"
    )

    # Assert 5: Golden similarity must meet threshold (if golden exists)
    if result.golden_similarity is not None:
        min_similarity = 0.4  # 40% similarity required
        assert result.golden_similarity >= min_similarity, (
            f"{result.pack_key} too dissimilar from golden response: "
            f"{result.golden_similarity:.2%} < {min_similarity:.0%}\n"
            f"Actual output deviates too much from ideal agency-grade format.\n\n"
            f"Diff (first 50 lines):\n{result.golden_diff}"
        )

    # If all assertions pass, the test succeeds
    print(f"\n✅ {result.pack_key} PASSED")
    print(f"   Brand mentions: {result.brand_mentions}")
    print(f"   Markdown length: {result.markdown_length}")
    print(f"   Stub used: {result.stub_used}")
    if result.golden_similarity is not None:
        print(f"   Golden similarity: {result.golden_similarity:.2%}")


# Legacy individual test functions for backwards compatibility
# (These now just call the parametrized test logic)
@pytest.mark.integration
def test_quick_social_basic_simulation():
    """Quick Social Pack (Basic) - D2C Beauty"""
    test_pack_meets_benchmark("pack_quick_social_basic_d2c.json")


@pytest.mark.integration
def test_strategy_campaign_basic_simulation():
    """Strategy + Campaign Pack (Basic) - Fitness"""
    test_pack_meets_benchmark("pack_strategy_campaign_basic_fitness.json")


@pytest.mark.integration
def test_strategy_campaign_standard_simulation():
    """Strategy + Campaign Pack (Standard) - Automotive"""
    test_pack_meets_benchmark("agency_report_automotive_luxotica.json")


@pytest.mark.integration
def test_strategy_campaign_premium_simulation():
    """Strategy + Campaign Pack (Premium) - EdTech"""
    test_pack_meets_benchmark("pack_strategy_campaign_premium_edtech.json")


@pytest.mark.integration
def test_strategy_campaign_enterprise_simulation():
    """Strategy + Campaign Pack (Enterprise) - Financial Services"""
    test_pack_meets_benchmark("pack_strategy_campaign_enterprise_financial.json")


@pytest.mark.integration
def test_full_funnel_growth_suite_simulation():
    """Full-Funnel Growth Suite - B2B SaaS"""
    test_pack_meets_benchmark("pack_full_funnel_growth_suite_saas.json")


@pytest.mark.integration
def test_launch_gtm_pack_simulation():
    """Launch & GTM Pack - Consumer Electronics"""
    test_pack_meets_benchmark("pack_launch_gtm_consumer_electronics.json")


@pytest.mark.integration
def test_brand_turnaround_lab_simulation():
    """Brand Turnaround Lab - Furniture"""
    test_pack_meets_benchmark("pack_brand_turnaround_furniture.json")


@pytest.mark.integration
def test_retention_crm_booster_simulation():
    """Retention & CRM Booster - Subscription Coffee"""
    test_pack_meets_benchmark("pack_retention_crm_coffee.json")


@pytest.mark.integration
def test_performance_audit_revamp_simulation():
    """Performance Audit & Revamp - Ecommerce Apparel"""
    test_pack_meets_benchmark("pack_performance_audit_activegear.json")


if __name__ == "__main__":
    """Run all simulations and print summary."""
    print("=" * 80)
    print("AICMO ALL-PACKS SIMULATION - REAL EXECUTION")
    print("=" * 80)
    print()

    # Check LLM configuration
    if LLM_CONFIGURED:
        print("✅ LLM CONFIGURED (tests will validate quality gates)")
    else:
        print("⚠️  NO LLM CONFIGURED (tests will be SKIPPED)")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY to enable LLM validation")
    print()

    benchmarks = ALL_BENCHMARK_FILES

    results = []
    for benchmark_file in benchmarks:
        print(f"Running: {benchmark_file}...")
        result = run_pack_simulation_sync(benchmark_file)
        results.append(result)

        # Determine status based on stub usage and success
        if result.stub_used:
            status = "🔶 STUB"
        elif result.success:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"

        print(f"{status} - {result.pack_key}: {result.reason[:100]}")
        print(f"       Stub used: {result.stub_used}, Brand mentions: {result.brand_mentions}")
        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    passed = sum(1 for r in results if r.success and not r.stub_used)
    failed = sum(1 for r in results if not r.success)
    stub_used = sum(1 for r in results if r.stub_used)

    print(f"Total: {len(results)}")
    print(f"Passed (real LLM): {passed}")
    print(f"Failed: {failed}")
    print(f"Stub content used: {stub_used}")
    print()

    if stub_used > 0:
        print("⚠️  STUB CONTENT WARNING:")
        print("   Tests using stub content cannot be considered valid passes.")
        print("   Configure LLM (OPENAI_API_KEY/ANTHROPIC_API_KEY) for real validation.")
        print()

    if failed > 0:
        print("FAILURES:")
        for r in results:
            if not r.success:
                print(f"  - {r.pack_key}: {r.reason}")
        print()

    if not LLM_CONFIGURED:
        print("❌ VALIDATION INCOMPLETE: No LLM configured")
        print("   Run pytest to see tests properly skipped.")
    elif stub_used == 0 and failed == 0:
        print("✅ ALL TESTS PASSED WITH REAL LLM CONTENT")
    else:
        print(f"⚠️  {failed + stub_used} of {len(results)} tests need attention")
