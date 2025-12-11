#!/usr/bin/env python3
"""
Self-Check Diagnostic Tool: Check provider health and get operator recommendations.

Usage:
    python3 scripts/run_self_check.py              # Run full health check
    python3 scripts/run_self_check.py --status     # Get current status only
    python3 scripts/run_self_check.py --watch      # Periodic checks (every 5 min)
    python3 scripts/run_self_check.py --help       # Show help

Requires:
    - AICMO environment setup
    - Provider credentials (if using real providers)
"""

import asyncio
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from aicmo.gateways import factory
from aicmo.monitoring import (
    get_self_check_service,
    get_registry,
)
from aicmo.core.config_gateways import get_gateway_config


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def print_section(text: str) -> None:
    """Print a formatted section header."""
    print(f"\n{text}")
    print(f"{'-' * len(text)}\n")


async def run_full_check() -> None:
    """Run comprehensive health check on all providers."""
    print_header("AICMO PROVIDER HEALTH CHECK")
    
    config = get_gateway_config()
    print(f"Configuration:")
    print(f"  • USE_REAL_GATEWAYS: {config.USE_REAL_GATEWAYS}")
    print(f"  • DRY_RUN_MODE: {config.DRY_RUN_MODE}")
    
    # Setup provider chains
    print(f"\nSetting up provider chains...")
    factory.setup_provider_chains(
        is_dry_run=config.DRY_RUN_MODE
    )
    
    # Run checks
    service = get_self_check_service()
    print(f"\nRunning health checks...")
    result = await service.run_full_check()
    
    # Display results
    print_section("RESULTS")
    summary = result.get('summary', {})
    print(f"  Total providers tracked: {summary.get('total_providers_tracked', 0)}")
    print(f"  Total checks recorded: {summary.get('total_checks_recorded', 0)}")
    print(f"  Success rate: {summary.get('success_rate_percent', 0):.1f}%")
    print(f"  Active recommendations: {summary.get('active_recommendations', 0)}")
    
    # Show recent checks
    recent = result.get('recent_checks', [])
    if recent:
        print_section("RECENT CHECKS (Last 5)")
        for check in recent:
            status = "✓" if check['success'] else "✗"
            latency = f" ({check['latency_ms']:.1f}ms)" if check.get('latency_ms') else ""
            print(f"  {status} {check['capability']}/{check['provider']}{latency}")
            if check.get('error'):
                print(f"      Error: {check['error']}")
    
    # Show recommendations
    recommendations = result.get('recommendations', [])
    if recommendations:
        print_section("OPERATOR RECOMMENDATIONS")
        for rec in recommendations:
            severity_icon = {
                'critical': '🚨',
                'warning': '⚠️',
                'info': 'ℹ️',
            }.get(rec['severity'], '❓')
            
            print(f"  {severity_icon} {rec['provider']} ({rec['status']})")
            print(f"      Issue: {rec['issue']}")
            print(f"      Action: {rec['action']}")
    else:
        print_section("STATUS")
        print("  ✓ All providers healthy - no recommendations at this time")
    
    print_header("END OF REPORT")


def show_current_status() -> None:
    """Show current provider status without running checks."""
    print_header("PROVIDER STATUS REPORT")
    
    registry = get_registry()
    report = registry.get_status_report()
    
    # Summary
    summary = report.get('summary', {})
    print("Summary:")
    print(f"  • Providers tracked: {summary.get('total_providers_tracked', 0)}")
    print(f"  • Total checks: {summary.get('total_checks_recorded', 0)}")
    print(f"  • Success rate: {summary.get('success_rate_percent', 0):.1f}%")
    print(f"  • Active issues: {summary.get('active_recommendations', 0)}")
    
    # Recent checks
    recent = report.get('recent_checks', [])
    if recent:
        print_section("Recent Checks")
        for check in recent:
            status = "✓" if check['success'] else "✗"
            print(f"  {status} {check['capability']}/{check['provider']}")
    else:
        print("\n  No checks recorded yet. Run 'python3 scripts/run_self_check.py' to start.")
    
    # Recommendations
    recommendations = report.get('recommendations', [])
    if recommendations:
        print_section("Active Recommendations")
        for rec in recommendations:
            print(f"  ⚠️  {rec['provider']}: {rec['action']}")
    
    print_header("END OF REPORT")


async def watch_mode(interval: int = 300) -> None:
    """Run periodic checks in watch mode."""
    print_header(f"WATCH MODE - Checking every {interval}s")
    print("Press Ctrl+C to stop\n")
    
    config = get_gateway_config()
    factory.setup_provider_chains(is_dry_run=config.DRY_RUN_MODE)
    
    service = get_self_check_service()
    
    try:
        await service.start_periodic_checks(interval_seconds=interval)
        
        # Keep running
        while True:
            await asyncio.sleep(60)
            
            # Show status every minute
            registry = get_registry()
            report = registry.get_status_report()
            summary = report.get('summary', {})
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Success rate: {summary.get('success_rate_percent', 0):.1f}% | "
                  f"Issues: {summary.get('active_recommendations', 0)}")
    
    except KeyboardInterrupt:
        print("\n\nStopping watch mode...")
        await service.stop_periodic_checks()
        print("✓ Stopped")


def export_json() -> None:
    """Export current status as JSON."""
    registry = get_registry()
    report = registry.get_status_report()
    
    print(json.dumps(report, indent=2, default=str))


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AICMO Provider Health Check & Diagnostics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full health check
  python3 scripts/run_self_check.py
  
  # Check current status (no new checks)
  python3 scripts/run_self_check.py --status
  
  # Run periodic checks
  python3 scripts/run_self_check.py --watch
  
  # Export status as JSON
  python3 scripts/run_self_check.py --json
        """,
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current status without running new checks",
    )
    
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run periodic health checks (every 5 minutes)",
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Export current status as JSON",
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Interval in seconds for watch mode (default: 300)",
    )
    
    args = parser.parse_args()
    
    try:
        if args.status:
            show_current_status()
        elif args.watch:
            asyncio.run(watch_mode(args.interval))
        elif args.json:
            export_json()
        else:
            # Default: run full check
            asyncio.run(run_full_check())
    
    except KeyboardInterrupt:
        print("\n\nAborted.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
