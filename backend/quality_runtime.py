"""
Runtime quality checks for AICMO pack outputs.

Applies lightweight quality validation at runtime using the same criteria
as test_all_packs_simulation.py to prevent broken/off-domain outputs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List


BENCHMARKS_DIR = Path(__file__).resolve().parent.parent / "learning" / "benchmarks"


@dataclass
class QualityCheckResult:
    """Result of runtime quality check."""

    passed: bool
    pack_key: str
    missing_required_terms: List[str]
    forbidden_terms_found: List[str]
    brand_mentions: int
    min_brand_mentions: int
    markdown_length: int
    min_markdown_length: int
    failure_reasons: List[str]


def load_benchmark_for_pack(pack_key: str) -> Optional[Dict[str, Any]]:
    """
    Load benchmark JSON for a given pack key.

    Args:
        pack_key: Pack identifier (e.g., "quick_social_basic")

    Returns:
        Benchmark dict or None if not found
    """
    # Try direct pack filename
    benchmark_file = BENCHMARKS_DIR / f"pack_{pack_key}.json"

    # Special case: strategy_campaign_standard uses different naming
    if pack_key == "strategy_campaign_standard" and not benchmark_file.exists():
        benchmark_file = BENCHMARKS_DIR / "agency_report_automotive_luxotica.json"

    if not benchmark_file.exists():
        return None

    try:
        with benchmark_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def check_runtime_quality(
    pack_key: str,
    markdown: str,
    brand_name: Optional[str] = None,
) -> QualityCheckResult:
    """
    Perform lightweight quality check on generated markdown.

    Uses same criteria as test_all_packs_simulation.py:
    - Required terms present
    - Forbidden terms absent
    - Minimum brand mentions
    - Minimum markdown length

    Args:
        pack_key: Pack identifier
        markdown: Generated markdown content
        brand_name: Brand name from brief (optional)

    Returns:
        QualityCheckResult with pass/fail and detailed reasons
    """
    # Load benchmark for this pack
    benchmark = load_benchmark_for_pack(pack_key)

    # If no benchmark found, pass by default (no criteria to check)
    if not benchmark:
        return QualityCheckResult(
            passed=True,
            pack_key=pack_key,
            missing_required_terms=[],
            forbidden_terms_found=[],
            brand_mentions=0,
            min_brand_mentions=0,
            markdown_length=len(markdown),
            min_markdown_length=0,
            failure_reasons=[],
        )

    markdown_lower = markdown.lower()
    failure_reasons = []

    # Check 1: Required terms
    required_terms = benchmark.get("required_terms", [])
    missing_terms = [term for term in required_terms if term.lower() not in markdown_lower]

    if missing_terms:
        failure_reasons.append(f"Missing required terms: {missing_terms}")

    # Check 2: Forbidden terms
    forbidden_terms = benchmark.get("forbidden_terms", [])
    found_forbidden = [term for term in forbidden_terms if term.lower() in markdown_lower]

    if found_forbidden:
        failure_reasons.append(f"Forbidden terms found: {found_forbidden}")

    # Check 3: Brand mentions
    benchmark_brand = benchmark.get("brand_name", brand_name or "")
    min_brand_mentions = benchmark.get("min_brand_mentions", 3)
    brand_mentions = markdown_lower.count(benchmark_brand.lower()) if benchmark_brand else 0

    if brand_mentions < min_brand_mentions:
        failure_reasons.append(
            f"Insufficient brand mentions: {brand_mentions} < {min_brand_mentions}"
        )

    # Check 4: Minimum markdown length (generic quality check)
    min_length = 1000  # Agency-grade reports should be substantial
    markdown_length = len(markdown)

    if markdown_length < min_length:
        failure_reasons.append(f"Output too short: {markdown_length} chars < {min_length} minimum")

    passed = len(failure_reasons) == 0

    return QualityCheckResult(
        passed=passed,
        pack_key=pack_key,
        missing_required_terms=missing_terms,
        forbidden_terms_found=found_forbidden,
        brand_mentions=brand_mentions,
        min_brand_mentions=min_brand_mentions,
        markdown_length=markdown_length,
        min_markdown_length=min_length,
        failure_reasons=failure_reasons,
    )
