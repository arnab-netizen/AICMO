#!/usr/bin/env python
"""
High-load simulation utility for AICMO Round 2 hardening.

Stress-tests the system with multiple synthetic briefs to identify bottlenecks:
- Generation time (stub + LLM modes)
- Validation performance
- Export speed (PDF, PPTX, ZIP)
- Memory usage trends

Usage:
    python scripts/run_highload_simulation.py --num-briefs 20 --verbose
"""

import argparse
import json
import logging
import sys
import time
from typing import List, Dict

# AICMO imports
from aicmo.io.client_reports import (
    ClientInputBrief,
    BrandBrief,
    AudienceBrief,
    GoalBrief,
    VoiceBrief,
    ProductServiceBrief,
    AssetsConstraintsBrief,
    OperationsBrief,
    StrategyExtrasBrief,
)
from backend.main import GenerateRequest, _generate_stub_output
from backend.export_utils import safe_export_pdf, safe_export_pptx, safe_export_zip
from aicmo.quality.validators import validate_report

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger("highload_sim")


def create_synthetic_brief(index: int) -> ClientInputBrief:
    """Create a realistic synthetic brief for testing."""
    industries = ["SaaS", "Retail", "Finance", "Healthcare", "EdTech"]
    goals = ["brand_awareness", "lead_generation", "sales", "retention", "engagement"]
    platforms = [
        ["LinkedIn", "Twitter"],
        ["Instagram", "TikTok"],
        ["Facebook", "YouTube"],
        ["LinkedIn", "Reddit"],
        ["Twitter", "Discord"],
    ]

    return ClientInputBrief(
        brand=BrandBrief(
            brand_name=f"TestBrand_{index}",
            industry=industries[index % len(industries)],
            brand_adjectives=["innovative", "reliable", "customer-focused"],
        ),
        audience=AudienceBrief(
            primary_customer=f"Customer Segment {index}",
            online_hangouts=platforms[index % len(platforms)],
        ),
        goal=GoalBrief(
            primary_goal=goals[index % len(goals)],
            timeline=f"Q{(index % 4) + 1} 2025",
        ),
        voice=VoiceBrief(),
        product_service=ProductServiceBrief(),
        assets_constraints=AssetsConstraintsBrief(),
        operations=OperationsBrief(),
        strategy_extras=StrategyExtrasBrief(
            success_30_days=f"Achieve {10 + index}% growth in {goals[index % len(goals)]}",
            brand_adjectives=["innovative", "trustworthy"],
        ),
    )


def benchmark_generation(briefs: List[ClientInputBrief], verbose: bool = False) -> Dict:
    """Benchmark report generation."""
    logger.info(f"Benchmarking generation for {len(briefs)} briefs...")

    times: List[float] = []
    errors = 0

    for i, brief in enumerate(briefs):
        try:
            req = GenerateRequest(brief=brief)

            start = time.time()
            _generate_stub_output(req)  # noqa: F841
            elapsed = time.time() - start

            times.append(elapsed)

            if verbose:
                logger.info(f"  Brief {i+1}/{len(briefs)}: {elapsed:.2f}s")

        except Exception as e:
            errors += 1
            if verbose:
                logger.error(f"  Brief {i+1} failed: {e}")

    return {
        "total_briefs": len(briefs),
        "successful": len(briefs) - errors,
        "errors": errors,
        "min_time": min(times) if times else 0,
        "max_time": max(times) if times else 0,
        "avg_time": sum(times) / len(times) if times else 0,
        "total_time": sum(times),
    }


def benchmark_validation(reports: List, verbose: bool = False) -> Dict:
    """Benchmark report validation."""
    logger.info(f"Benchmarking validation for {len(reports)} reports...")

    times: List[float] = []
    errors = 0
    blocking_issues = 0

    for i, report in enumerate(reports):
        try:
            start = time.time()
            issues = validate_report(report)
            elapsed = time.time() - start

            times.append(elapsed)

            # Count blocking issues
            if issues:
                blocking = [x for x in issues if x.severity == "error"]
                if blocking:
                    blocking_issues += 1

            if verbose:
                logger.info(
                    f"  Report {i+1}/{len(reports)}: {elapsed:.3f}s, {len(issues)} issue(s)"
                )

        except Exception as e:
            errors += 1
            if verbose:
                logger.error(f"  Report {i+1} failed: {e}")

    return {
        "total_reports": len(reports),
        "successful": len(reports) - errors,
        "errors": errors,
        "blocking_issues": blocking_issues,
        "min_time": min(times) if times else 0,
        "max_time": max(times) if times else 0,
        "avg_time": sum(times) / len(times) if times else 0,
        "total_time": sum(times),
    }


def benchmark_exports(briefs: List, reports: List, verbose: bool = False) -> Dict:
    """Benchmark export functions."""
    logger.info(f"Benchmarking exports for {len(briefs)} briefs and reports...")

    results = {
        "pdf": {"successful": 0, "errors": 0, "total_bytes": 0, "times": []},
        "pptx": {"successful": 0, "errors": 0, "total_bytes": 0, "times": []},
        "zip": {"successful": 0, "errors": 0, "total_bytes": 0, "times": []},
    }

    for i, (brief, report) in enumerate(zip(briefs, reports)):
        # PDF export
        try:
            from aicmo.io.client_reports import generate_output_report_markdown

            markdown = generate_output_report_markdown(brief, report)
            start = time.time()
            result = safe_export_pdf(markdown, check_placeholders=False)
            elapsed = time.time() - start

            if not isinstance(result, dict):  # StreamingResponse
                results["pdf"]["successful"] += 1
                results["pdf"]["total_bytes"] += len(markdown.encode())
                results["pdf"]["times"].append(elapsed)
            else:
                results["pdf"]["errors"] += 1
        except Exception as e:
            results["pdf"]["errors"] += 1
            if verbose:
                logger.error(f"  PDF export {i+1} failed: {e}")

        # PPTX export
        try:
            start = time.time()
            result = safe_export_pptx(brief, report, check_placeholders=False)
            elapsed = time.time() - start

            if not isinstance(result, dict):  # StreamingResponse
                results["pptx"]["successful"] += 1
                results["pptx"]["times"].append(elapsed)
            else:
                results["pptx"]["errors"] += 1
        except Exception as e:
            results["pptx"]["errors"] += 1
            if verbose:
                logger.error(f"  PPTX export {i+1} failed: {e}")

        # ZIP export
        try:
            start = time.time()
            result = safe_export_zip(brief, report, check_placeholders=False)
            elapsed = time.time() - start

            if not isinstance(result, dict):  # StreamingResponse
                results["zip"]["successful"] += 1
                results["zip"]["times"].append(elapsed)
            else:
                results["zip"]["errors"] += 1
        except Exception as e:
            results["zip"]["errors"] += 1
            if verbose:
                logger.error(f"  ZIP export {i+1} failed: {e}")

        if verbose and (i + 1) % max(1, len(briefs) // 5) == 0:
            logger.info(f"  Export {i+1}/{len(briefs)} complete")

    # Compute stats
    for fmt in ["pdf", "pptx", "zip"]:
        times = results[fmt]["times"]
        if times:
            results[fmt]["min_time"] = min(times)
            results[fmt]["max_time"] = max(times)
            results[fmt]["avg_time"] = sum(times) / len(times)
            results[fmt]["total_time"] = sum(times)
        else:
            results[fmt]["min_time"] = 0
            results[fmt]["max_time"] = 0
            results[fmt]["avg_time"] = 0
            results[fmt]["total_time"] = 0

        # Clean up times list for JSON serialization
        del results[fmt]["times"]

    return results


def main():
    """Run high-load simulation."""
    parser = argparse.ArgumentParser(description="High-load simulation for AICMO Round 2 hardening")
    parser.add_argument(
        "--num-briefs",
        type=int,
        default=10,
        help="Number of synthetic briefs to test (default: 10)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--skip-exports",
        action="store_true",
        help="Skip export benchmarking (slow)",
    )
    parser.add_argument(
        "--output-json",
        help="Output results as JSON to file",
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("AICMO Round 2 High-Load Simulation")
    logger.info("=" * 70)

    # Generate synthetic briefs
    logger.info(f"\nGenerating {args.num_briefs} synthetic briefs...")
    briefs = [create_synthetic_brief(i) for i in range(args.num_briefs)]
    logger.info(f"✓ Generated {len(briefs)} briefs")

    # Benchmark generation
    logger.info("\n" + "=" * 70)
    gen_results = benchmark_generation(briefs, verbose=args.verbose)
    logger.info(f"Generation: {gen_results['successful']}/{gen_results['total_briefs']} successful")
    logger.info(f"  Avg time: {gen_results['avg_time']:.2f}s")
    logger.info(f"  Total time: {gen_results['total_time']:.2f}s")

    # Generate reports for validation/export
    logger.info("\nGenerating reports for validation...")
    reports = []
    for brief in briefs:
        try:
            req = GenerateRequest(brief=brief)
            report = _generate_stub_output(req)
            reports.append(report)
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")

    # Benchmark validation
    logger.info("\n" + "=" * 70)
    val_results = benchmark_validation(reports, verbose=args.verbose)
    logger.info(
        f"Validation: {val_results['successful']}/{val_results['total_reports']} successful"
    )
    logger.info(f"  Blocking issues found: {val_results['blocking_issues']}")
    logger.info(f"  Avg time: {val_results['avg_time']:.3f}s")
    logger.info(f"  Total time: {val_results['total_time']:.2f}s")

    # Benchmark exports (optional)
    export_results = None
    if not args.skip_exports:
        logger.info("\n" + "=" * 70)
        export_results = benchmark_exports(briefs, reports, verbose=args.verbose)
        for fmt in ["pdf", "pptx", "zip"]:
            logger.info(f"{fmt.upper()}: {export_results[fmt]['successful']} successful")
            logger.info(f"  Avg time: {export_results[fmt]['avg_time']:.2f}s")
            logger.info(f"  Total time: {export_results[fmt]['total_time']:.2f}s")

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    total_ops = gen_results["successful"] + val_results["successful"]
    if export_results:
        total_ops += sum(f["successful"] for f in export_results.values())
    total_time = gen_results["total_time"] + val_results["total_time"]
    if export_results:
        total_time += sum(f["total_time"] for f in export_results.values())

    logger.info(f"Total operations: {total_ops}")
    logger.info(f"Total time: {total_time:.2f}s")
    logger.info(f"Throughput: {total_ops / total_time:.1f} ops/sec")

    # Output JSON if requested
    if args.output_json:
        output = {
            "generation": gen_results,
            "validation": val_results,
            "exports": export_results,
            "summary": {
                "total_operations": total_ops,
                "total_time": total_time,
                "throughput": total_ops / total_time if total_time > 0 else 0,
            },
        }
        with open(args.output_json, "w") as f:
            json.dump(output, f, indent=2)
        logger.info(f"\nResults saved to {args.output_json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
