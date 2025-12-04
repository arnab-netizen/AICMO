"""
Non-Regression Snapshot Utility for Quick Social Pack

Purpose: Generate JSON snapshots of Quick Social Pack output for
comparison during refactoring and future development.

Use Cases:
    1. Before refactoring: Create baseline snapshot
    2. After refactoring: Compare against baseline
    3. CI/CD: Automated regression detection
    4. Documentation: Track changes over time

Usage:
    # Create a snapshot
    python -c "from backend.utils.non_regression_snapshot import create_snapshot; create_snapshot()"
    
    # Compare two snapshots
    python -c "from backend.utils.non_regression_snapshot import compare_snapshots; compare_snapshots('snapshot1.json', 'snapshot2.json')"
    
    # Generate report
    python backend/utils/non_regression_snapshot.py
"""

import os
import sys
import json
import hashlib
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Force disable stub mode
os.environ["AICMO_STUB_MODE"] = "0"
os.environ["AICMO_USE_LLM"] = "false"

sys.path.insert(0, "/workspaces/AICMO")

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


def create_test_brief() -> ClientInputBrief:
    """Create consistent test brief for snapshot generation."""
    brand = BrandBrief(
        brand_name="SnapshotTest Brand",
        industry="Technology",
        product_service="Software solutions for modern teams",
        primary_goal="Increase brand awareness and customer acquisition",
        primary_customer="Tech professionals and businesses",
        location="Seattle, USA",
        timeline="90 days",
        brand_tone="Professional, innovative, trustworthy",
    ).with_safe_defaults()

    return ClientInputBrief(
        brand=brand,
        audience=AudienceBrief(primary_customer="Business professionals aged 25-45"),
        goal=GoalBrief(
            primary_goal="Increase brand awareness and customer acquisition",
            timeline="90 days",
            kpis=["social engagement", "website traffic", "lead generation"],
        ),
        voice=VoiceBrief(tone_of_voice=["professional", "innovative", "trustworthy"]),
        product_service=ProductServiceBrief(),
        assets_constraints=AssetsConstraintsBrief(focus_platforms=["LinkedIn", "Twitter"]),
        operations=OperationsBrief(),
        strategy_extras=StrategyExtrasBrief(),
    )


def generate_snapshot_data() -> Dict[str, Any]:
    """Generate Quick Social Pack and extract snapshot data."""
    brief = create_test_brief()
    req = GenerateRequest(brief=brief, wow_package_key="quick_social_basic")
    result = asyncio.run(aicmo_generate(req))

    snapshot = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "pack_key": "quick_social_basic",
            "brief_brand": brief.brand.brand_name,
        },
        "content": {
            "raw_markdown": result.raw_markdown,
            "word_count": len(result.raw_markdown.split()),
            "char_count": len(result.raw_markdown),
            "line_count": len(result.raw_markdown.split("\n")),
            "content_hash": hashlib.md5(result.raw_markdown.encode()).hexdigest(),
        },
        "metrics": {},
    }

    # Calculate aggregate metrics
    snapshot["metrics"]["total_word_count"] = snapshot["content"]["word_count"]
    snapshot["metrics"]["total_char_count"] = snapshot["content"]["char_count"]
    snapshot["metrics"]["total_line_count"] = snapshot["content"]["line_count"]

    return snapshot


def create_snapshot(output_path: Optional[str] = None) -> str:
    """
    Create a snapshot file of current Quick Social Pack output.

    Args:
        output_path: Optional custom path for snapshot file

    Returns:
        Path to created snapshot file
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"snapshots/quick_social_snapshot_{timestamp}.json"

    # Create snapshots directory if needed
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    snapshot = generate_snapshot_data()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    print(f"✅ Snapshot created: {output_path}")
    print(f"   Sections: {snapshot['metrics']['section_count']}")
    print(f"   Total words: {snapshot['metrics']['total_word_count']}")

    return output_path


def load_snapshot(snapshot_path: str) -> Dict[str, Any]:
    """Load a snapshot from JSON file."""
    with open(snapshot_path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_snapshots(
    baseline_path: str, current_path: str, verbose: bool = True
) -> Dict[str, Any]:
    """
    Compare two snapshots and report differences.

    Args:
        baseline_path: Path to baseline snapshot
        current_path: Path to current snapshot
        verbose: Print detailed comparison report

    Returns:
        Dictionary with comparison results
    """
    baseline = load_snapshot(baseline_path)
    current = load_snapshot(current_path)

    comparison = {
        "baseline_timestamp": baseline["metadata"]["timestamp"],
        "current_timestamp": current["metadata"]["timestamp"],
        "content_modified": False,
        "metrics_delta": {},
    }

    # Compare content hashes
    baseline_hash = baseline["content"]["content_hash"]
    current_hash = current["content"]["content_hash"]

    comparison["content_modified"] = baseline_hash != current_hash
    comparison["content_delta"] = {
        "word_count": current["content"]["word_count"] - baseline["content"]["word_count"],
        "char_count": current["content"]["char_count"] - baseline["content"]["char_count"],
        "line_count": current["content"]["line_count"] - baseline["content"]["line_count"],
    }

    # Compare metrics
    for metric_name in ["total_word_count", "total_char_count", "total_line_count"]:
        baseline_value = baseline["metrics"][metric_name]
        current_value = current["metrics"][metric_name]
        comparison["metrics_delta"][metric_name] = {
            "baseline": baseline_value,
            "current": current_value,
            "delta": current_value - baseline_value,
        }

    if verbose:
        print_comparison_report(comparison)

    return comparison


def print_comparison_report(comparison: Dict[str, Any]):
    """Print human-readable comparison report."""
    print("=" * 70)
    print("QUICK SOCIAL PACK - SNAPSHOT COMPARISON")
    print("=" * 70)
    print()
    print(f"Baseline: {comparison['baseline_timestamp']}")
    print(f"Current:  {comparison['current_timestamp']}")
    print()

    # Content changes
    if comparison["content_modified"]:
        print("📝 CONTENT MODIFIED:")
        delta = comparison["content_delta"]
        print(f"   Word count: {delta['word_count']:+d}")
        print(f"   Char count: {delta['char_count']:+d}")
        print(f"   Line count: {delta['line_count']:+d}")
        print()
    else:
        print("✅ CONTENT IDENTICAL - No changes detected")
        print()

    # Metrics delta
    print("📊 METRICS DELTA:")
    for metric_name, metric_data in comparison["metrics_delta"].items():
        baseline = metric_data["baseline"]
        current = metric_data["current"]
        delta = metric_data["delta"]
        pct_change = (delta / baseline * 100) if baseline > 0 else 0

        print(f"   {metric_name}:")
        print(
            f"     Baseline: {baseline} | Current: {current} | Delta: {delta:+d} ({pct_change:+.1f}%)"
        )

    print()
    print("=" * 70)

    # Summary verdict
    if not comparison["content_modified"]:
        print("✅ NO CHANGES DETECTED - Output is identical")
    else:
        print("⚠️  CHANGES DETECTED - Review modifications carefully")

    print("=" * 70)


def generate_report():
    """Generate a new snapshot and comparison report (if baseline exists)."""
    baseline_path = "snapshots/quick_social_baseline.json"

    # Create new snapshot
    print("Generating current snapshot...")
    current_path = create_snapshot("snapshots/quick_social_current.json")
    print()

    # Compare to baseline if exists
    if Path(baseline_path).exists():
        print("Comparing to baseline...")
        compare_snapshots(baseline_path, current_path)
    else:
        print(f"ℹ️  No baseline found at {baseline_path}")
        print(
            "   To create baseline: mv snapshots/quick_social_current.json snapshots/quick_social_baseline.json"
        )


if __name__ == "__main__":
    generate_report()
