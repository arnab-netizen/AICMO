"""
Self-Test Engine CLI

Command-line interface for running self-tests.
"""

import os
import sys
from pathlib import Path
from typing import Optional

from aicmo.self_test.orchestrator import SelfTestOrchestrator
from aicmo.self_test.reporting import ReportGenerator


def main(
    quick_mode: bool = True,
    output_dir: str = "/workspaces/AICMO/self_test_artifacts",
    verbose: bool = False,
    enable_quality: Optional[bool] = None,
    enable_layout: Optional[bool] = None,
    enable_format: Optional[bool] = None,
    benchmarks_only: bool = False,
    project_rehearsal: bool = False,
    deterministic: bool = False,
    flakiness_check: bool = False,
) -> int:
    """
    Run self-test engine from CLI.

    Args:
        quick_mode: If True, limit test scope for faster execution
        output_dir: Directory to save reports
        verbose: If True, print detailed output
        enable_quality: If True, enable quality checks; None = use env var or default
        enable_layout: If True, enable layout checks; None = use env var or default
        enable_format: If True, enable format/word-count checks; None = use env var or default
        benchmarks_only: If True, only check benchmarks (skip other tests)
        project_rehearsal: If True, run full project rehearsal simulations
        deterministic: If True, use stub/fixed-seed mode for reproducibility
        flakiness_check: If True, run 2-3 iterations in deterministic mode to check for flakiness

    Returns:
        Exit code (0 for success, 1 for failures)
    """
    print("🚀 Starting AICMO Self-Test Engine v2.0...\n")

    # Determine which checks are enabled
    if enable_quality is None:
        enable_quality = os.getenv("AICMO_SELF_TEST_ENABLE_QUALITY", "true").lower() == "true"
    if enable_layout is None:
        enable_layout = os.getenv("AICMO_SELF_TEST_ENABLE_LAYOUT", "true").lower() == "true"
    if enable_format is None:
        enable_format = os.getenv("AICMO_SELF_TEST_ENABLE_FORMAT", "true").lower() == "true"

    try:
        # Initialize orchestrator
        orchestrator = SelfTestOrchestrator()

        # Run self-test
        print("⏳ Running discovery and tests...")
        if verbose:
            print(f"   - Quality checks: {'enabled' if enable_quality else 'disabled'}")
            print(f"   - Layout checks: {'enabled' if enable_layout else 'disabled'}")
            print(f"   - Format checks: {'enabled' if enable_format else 'disabled'}")
            print(f"   - Benchmarks only: {benchmarks_only}")
            if deterministic:
                print(f"   - Deterministic mode: ENABLED (stub outputs, fixed seeds)")
            if flakiness_check:
                print(f"   - Flakiness check: ENABLED (running multiple iterations)")

        # Flakiness check mode: run multiple times and compare
        if flakiness_check:
            print("\n🔁 Running flakiness check (3 iterations in deterministic mode)...\n")
            deterministic = True  # Force deterministic for flakiness check
            
            flakiness_iterations = 3
            iteration_results = []
            feature_outputs = {}  # Track outputs per feature per iteration
            
            for i in range(flakiness_iterations):
                if verbose:
                    print(f"   Iteration {i+1}/{flakiness_iterations}...", end=" ")
                
                # Run test
                iter_result = orchestrator.run_self_test(
                    quick_mode=quick_mode,
                    enable_quality_checks=enable_quality,
                    enable_layout_checks=enable_layout,
                    enable_format_checks=enable_format,
                    benchmarks_only=benchmarks_only,
                    deterministic=True,
                )
                iteration_results.append(iter_result)
                
                # Track feature outputs for comparison
                for feature in iter_result.features:
                    if feature.name not in feature_outputs:
                        feature_outputs[feature.name] = []
                    # Use status + error count + warning count as signature
                    signature = (feature.status.value, len(feature.errors), len(feature.warnings))
                    feature_outputs[feature.name].append(signature)
                
                if verbose:
                    print(f"✓")
            
            # Detect flakiness: features with different outputs across runs
            flaky_features = []
            for feature_name, signatures in feature_outputs.items():
                if len(set(signatures)) > 1:
                    flaky_features.append(feature_name)
            
            # Store flakiness results
            result = iteration_results[-1]  # Use last iteration as main result
            result.flakiness_check_results = {
                fname: [str(s) for s in sigs] 
                for fname, sigs in feature_outputs.items() 
                if fname in flaky_features
            }
            
            if verbose:
                if flaky_features:
                    print(f"\n⚠️  Flakiness detected in: {', '.join(flaky_features)}\n")
                else:
                    print(f"\n✅ No flakiness detected - all features deterministic\n")
        else:
            result = orchestrator.run_self_test(
                quick_mode=quick_mode,
                enable_quality_checks=enable_quality,
                enable_layout_checks=enable_layout,
                enable_format_checks=enable_format,
                benchmarks_only=benchmarks_only,
                deterministic=deterministic,
            )

        # Run project rehearsal if requested
        if project_rehearsal:
            print("\n📋 Running Full Project Rehearsals...")
            from aicmo.self_test.test_inputs import get_quick_test_briefs
            
            briefs = get_quick_test_briefs()
            for brief in briefs[:2]:  # Run first 2 briefs
                if verbose:
                    print(f"   - Rehearsing: {brief.brand.brand_name}")
                rehearsal = orchestrator.run_full_project_rehearsal(
                    brief, 
                    project_name=brief.brand.brand_name
                )
                result.project_rehearsals.append(rehearsal)
                if verbose:
                    status = "✅ PASS" if rehearsal.passed else "❌ FAIL"
                    print(f"     {status} ({rehearsal.passed_steps}/{rehearsal.total_steps} steps)")


        # Generate reports
        print("📊 Generating reports...")
        reporter = ReportGenerator(output_dir)
        md_path, html_path = reporter.save_reports(result)

        # Print summary
        print("\n" + "=" * 60)
        print("AICMO SELF-TEST RESULTS")
        print("=" * 60)
        print(f"✅ Features Passed:  {result.passed_features}")
        print(f"❌ Features Failed:  {result.failed_features}")
        print(f"⏭️  Features Skipped: {result.skipped_features}")
        print("=" * 60)

        # Print coverage if available
        if result.coverage_info:
            print(f"\n📊 Coverage Metrics:")
            print(f"   - Benchmarks: {result.coverage_info.enforced_benchmarks}/{result.coverage_info.mapped_benchmarks} enforced")
            print(f"   - HTML layout: {'✅' if result.coverage_info.html_layout_checked else '❌'}")
            print(f"   - PPTX layout: {'✅' if result.coverage_info.pptx_layout_checked else '❌'}")
            print(f"   - PDF layout: {'✅' if result.coverage_info.pdf_layout_checked else '❌'}")
            print(f"   - Quality checks: {'enabled' if result.coverage_info.quality_checks_enabled else 'disabled'}")
            print(f"   - Format checks: {'enabled' if result.coverage_info.format_checks_enabled else 'disabled'}")

        print(f"\n📄 Markdown Report: {md_path}")
        print(f"🌐 HTML Report:     {html_path}\n")

        # Determine exit code based on critical failures
        if result.critical_failures:
            print("⚠️  CRITICAL FAILURES DETECTED:")
            for failure in result.critical_failures:
                print(f"   - {failure}")
            print("\n❌ Critical features failed - exiting with error code 1\n")
            return 1
        elif result.failed_features > 0:
            print("⚠️  OPTIONAL FEATURES FAILED (non-critical):")
            for feature in result.features:
                if feature.status.value == "fail" and not feature.critical:
                    print(f"   - {feature.name}: {', '.join(feature.errors) if feature.errors else 'Unknown error'}")
            print("\n✅ No critical failures - exiting with success code 0\n")
            return 0
        else:
            print("✅ All features passed - exiting with success code 0\n")
            return 0

    except Exception as e:
        print(f"\n❌ Error running self-test: {str(e)}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run AICMO Self-Test Engine v2.0",
        epilog="""
Environment Variables:
  AICMO_SELF_TEST_ENABLE_QUALITY  Set to 'false' to disable quality checks (default: true)
  AICMO_SELF_TEST_ENABLE_LAYOUT   Set to 'false' to disable layout checks (default: true)

Examples:
  python -m aicmo.self_test.cli --full
  python -m aicmo.self_test.cli --full --no-quality
  python -m aicmo.self_test.cli --benchmarks-only
  AICMO_SELF_TEST_ENABLE_QUALITY=false python -m aicmo.self_test.cli
        """
    )
    parser.add_argument(
        "--full",
        action="store_false",
        dest="quick",
        help="Run full test suite (slower, more thorough). Default is quick mode."
    )
    parser.add_argument(
        "--quality",
        action="store_true",
        dest="enable_quality",
        help="Enable quality checks (checks content genericity, placeholders, etc.)"
    )
    parser.add_argument(
        "--no-quality",
        action="store_false",
        dest="enable_quality",
        help="Disable quality checks"
    )
    parser.add_argument(
        "--layout",
        action="store_true",
        dest="enable_layout",
        help="Enable layout checks for HTML/PPTX/PDF"
    )
    parser.add_argument(
        "--no-layout",
        action="store_false",
        dest="enable_layout",
        help="Disable layout checks"
    )
    parser.add_argument(
        "--format",
        action="store_true",
        dest="enable_format",
        help="Enable format/word-count checks for text fields"
    )
    parser.add_argument(
        "--no-format",
        action="store_false",
        dest="enable_format",
        help="Disable format/word-count checks"
    )
    parser.add_argument(
        "--benchmarks-only",
        action="store_true",
        help="Only check benchmarks coverage (skip other tests)"
    )
    parser.add_argument(
        "--project-rehearsal",
        action="store_true",
        help="Run full project rehearsal simulations (brief → generators → packagers → artifacts)"
    )
    parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Use stub/fixed-seed mode for deterministic, reproducible outputs"
    )
    parser.add_argument(
        "--flakiness-check",
        action="store_true",
        help="Run 2-3 iterations in deterministic mode to detect flaky features"
    )
    parser.add_argument(
        "--output",
        default="/workspaces/AICMO/self_test_artifacts",
        help="Output directory for reports (default: /workspaces/AICMO/self_test_artifacts)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print verbose output including debug info"
    )

    args = parser.parse_args()

    exit_code = main(
        quick_mode=args.quick,
        output_dir=args.output,
        verbose=args.verbose,
        enable_quality=args.enable_quality,
        enable_layout=args.enable_layout,
        enable_format=args.enable_format,
        benchmarks_only=args.benchmarks_only,
        project_rehearsal=args.project_rehearsal,
        deterministic=args.deterministic,
        flakiness_check=args.flakiness_check,
    )
    sys.exit(exit_code)

