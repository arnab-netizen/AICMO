#!/usr/bin/env python3
"""
Debug helper to reproduce benchmark validation failures with REAL production payloads.

This script simulates the exact conditions under which sections fail in production:
- Full LLM refinement with Balanced mode (passes=2)
- Agency grade enhancements
- Humanization layer
- Research integration
- All services enabled

Usage:
    python -m backend.debug.print_benchmark_issues_with_payload full_funnel_growth_suite full_30_day_calendar
    
    Or with custom brief:
    python -m backend.debug.print_benchmark_issues_with_payload full_funnel_growth_suite full_30_day_calendar --brief luxotica
"""

import logging
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def get_luxotica_brief() -> Dict[str, Any]:
    """Return the Luxotica Automobiles brief that caused the real failure."""
    return {
        "brand_name": "Luxotica Automobiles",
        "industry": "Luxury Car Dealership",
        "product_service": "Premium luxury vehicles (Mercedes-Benz, BMW, Audi) with white-glove concierge service",
        "primary_customer": "High-net-worth individuals aged 35-55 in Kolkata seeking premium automotive experiences",
        "geography": "Kolkata, West Bengal, India",
        "primary_goal": "Increase test drive bookings by 40% and qualified leads by 60% within 90 days",
        "timeline": "90 days",
        "current_channels": "Instagram, Facebook, Google Search Ads, Email Marketing",
        "budget_range": "$15,000 - $25,000",
        "brand_voice": "Sophisticated, aspirational, trustworthy - speaks to success and refined taste",
        "raw_brief_text": """Luxotica Automobiles is Kolkata's premier luxury car dealership specializing in Mercedes-Benz, BMW, and Audi. 
        We serve high-net-worth individuals who value premium experiences and white-glove service. 
        Our goal is to increase test drive bookings by 40% and generate 60% more qualified leads within 90 days. 
        We need a comprehensive full-funnel strategy targeting successful professionals aged 35-55 who appreciate 
        luxury automotive excellence and personalized concierge service.""",
        "constraints": "Must maintain premium brand positioning, avoid discounting messaging",
        "competitors": "Landmark Cars, Big Boy Toyz, other luxury dealerships in Kolkata",
        "unique_selling_proposition": "White-glove concierge service with personalized vehicle delivery, lifetime maintenance packages, exclusive test drive experiences",
    }


def get_test_brief_generic() -> Dict[str, Any]:
    """Return a generic test brief for comparison."""
    return {
        "brand_name": "TestBrand",
        "industry": "Technology",
        "product_service": "SaaS platform",
        "primary_customer": "Small business owners",
        "geography": "United States",
        "primary_goal": "Increase sign-ups",
        "timeline": "60 days",
        "current_channels": "Social media, email",
        "budget_range": "$5,000 - $10,000",
        "brand_voice": "Professional and friendly",
    }


def main():
    """Run benchmark validation with real production payload."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test benchmark validation with real production payloads"
    )
    parser.add_argument(
        "pack_key",
        help="Pack key to test (e.g., full_funnel_growth_suite)",
    )
    parser.add_argument(
        "section_id",
        nargs="?",
        default=None,
        help="Specific section to test (optional, tests all if omitted)",
    )
    parser.add_argument(
        "--brief",
        choices=["luxotica", "generic"],
        default="luxotica",
        help="Which test brief to use",
    )
    parser.add_argument(
        "--no-refinement",
        action="store_true",
        help="Disable LLM refinement (test template only)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show full section content",
    )

    args = parser.parse_args()

    # Import here to avoid circular dependencies
    from backend.main import api_aicmo_generate_report
    from backend.validators.benchmark_validator import BenchmarkValidator

    log.info("=" * 80)
    log.info(f"BENCHMARK VALIDATION WITH REAL PAYLOAD: {args.pack_key}")
    log.info("=" * 80)

    # Select brief
    if args.brief == "luxotica":
        client_brief = get_luxotica_brief()
        log.info("📋 Using Luxotica Automobiles brief (real failure case)")
    else:
        client_brief = get_test_brief_generic()
        log.info("📋 Using generic test brief")

    log.info(f"   Brand: {client_brief['brand_name']}")
    log.info(f"   Industry: {client_brief['industry']}")
    log.info(f"   Goal: {client_brief['primary_goal']}")

    # Construct the EXACT payload that fails in production
    payload = {
        "client_brief": client_brief,
        "pack_key": args.pack_key,
        "wow_enabled": True,
        "wow_package_key": args.pack_key,
        "stage": "draft",
        "services": {
            "marketing_plan": True,
            "campaign_blueprint": True,
            "social_calendar": True,
            "performance_review": True,
            "creatives": True,
            "include_agency_grade": True,
        },
        "refinement_mode": {
            "name": "Balanced" if not args.no_refinement else "Minimal",
            "passes": 2 if not args.no_refinement else 1,
            "max_tokens": 12000,
            "temperature": 0.7,
        },
    }

    if args.no_refinement:
        log.info("🔧 LLM refinement DISABLED (testing template only)")
    else:
        log.info("🔧 LLM refinement ENABLED (Balanced mode, passes=2)")

    log.info("")
    log.info("🔄 Generating report with production settings...")

    try:
        # Generate report using the real API entrypoint
        result = api_aicmo_generate_report(payload)

        if not result.get("success"):
            log.error(f"❌ Report generation failed: {result.get('error', 'Unknown error')}")
            return 1

        log.info("✅ Report generated successfully")

        # Extract sections
        sections_data = result.get("sections", {})

        if args.section_id:
            section_ids_to_test = [args.section_id]
        else:
            section_ids_to_test = list(sections_data.keys())

        log.info(f"🔍 Testing {len(section_ids_to_test)} section(s) against benchmarks...")
        log.info("")

        # Load benchmarks
        validator = BenchmarkValidator(pack_key=args.pack_key)

        failures = []
        passes = []

        for section_id in section_ids_to_test:
            if section_id not in sections_data:
                log.warning(f"⚠️  Section '{section_id}' not found in generated report")
                continue

            section_text = sections_data[section_id]

            log.info("-" * 80)
            log.info(f"Section: {section_id}")
            log.info(f"Length: {len(section_text)} characters, {len(section_text.split())} words")

            if args.verbose:
                log.info("")
                log.info("Content preview (first 500 chars):")
                log.info(section_text[:500] + ("..." if len(section_text) > 500 else ""))
                log.info("")

            # Run benchmark validation
            try:
                issues = validator.validate_section(section_id, section_text)

                if not issues:
                    log.info("✅ PASS - No benchmark violations")
                    passes.append(section_id)
                else:
                    log.error(f"❌ FAIL - {len(issues)} benchmark violation(s):")
                    for issue in issues:
                        log.error(f"   - {issue['severity']}: {issue['message']}")
                        if "details" in issue:
                            for key, val in issue["details"].items():
                                log.error(f"     {key}: {val}")
                    failures.append((section_id, issues))

            except Exception as e:
                log.error(f"❌ FAIL - Validation error: {e}")
                failures.append((section_id, [{"message": str(e)}]))

        # Summary
        log.info("")
        log.info("=" * 80)
        log.info("VALIDATION SUMMARY")
        log.info("=" * 80)
        log.info(f"Passing Sections: {len(passes)}")
        log.info(f"Failing Sections: {len(failures)}")

        if failures:
            log.info("")
            log.info("Failed sections:")
            for section_id, issues in failures:
                log.info(f"  - {section_id}: {len(issues)} issue(s)")
            return 1
        else:
            log.info("")
            log.info("✅ ALL SECTIONS PASSED BENCHMARK VALIDATION")
            return 0

    except Exception as e:
        log.exception(f"❌ Fatal error during validation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
