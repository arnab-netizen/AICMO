#!/usr/bin/env python3
"""
Comprehensive Pack Hardening Validation Script.

Tests ALL packs (excluding already-hardened quick_social_basic and strategy_campaign_standard)
to identify which sections need fixing.

Packs to test:
1. launch_gtm_pack (13 sections)
2. brand_turnaround_lab (14 sections)
3. retention_crm_booster (14 sections)
4. performance_audit_revamp (16 sections)
5. full_funnel_growth_suite (23 sections)

Total: 80 sections to harden
"""

import os
import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent))

# Force template-only mode for testing
os.environ["OPENAI_API_KEY"] = "sk-test-fake-key"
os.environ["AICMO_USE_LLM"] = "false"
os.environ["AICMO_PERPLEXITY_ENABLED"] = "false"
os.environ["AICMO_STUB_MODE"] = "0"

from backend.main import GenerateRequest, aicmo_generate
from aicmo.io.client_reports import BrandBrief, GoalBrief
from backend.utils.wow_markdown_parser import parse_wow_markdown_to_sections
from backend.validators.report_gate import validate_report_sections


def create_test_brief(pack_name: str) -> GenerateRequest:
    """Create pack-specific test brief."""

    # Pack-specific brand contexts
    pack_contexts = {
        "launch_gtm_pack": {
            "brand_name": "LaunchPro",
            "industry": "B2B SaaS - Project Management",
            "value_prop": "AI-powered launch management platform for product teams",
            "goal": "Launch new AI Launch Assistant feature to 50K users in 90 days",
        },
        "brand_turnaround_lab": {
            "brand_name": "ReviveCo",
            "industry": "Consumer Electronics - Audio",
            "value_prop": "Premium wireless headphones with declining market share",
            "goal": "Rebuild brand reputation and regain 15% market share in 120 days",
        },
        "retention_crm_booster": {
            "brand_name": "KeepCust",
            "industry": "E-commerce - Fashion",
            "value_prop": "Sustainable fashion marketplace with high churn rate",
            "goal": "Reduce churn by 40% and increase repeat purchase rate to 45% in 90 days",
        },
        "performance_audit_revamp": {
            "brand_name": "OptimizeAds",
            "industry": "B2C - Online Education",
            "value_prop": "Professional certification courses with underperforming paid campaigns",
            "goal": "Reduce CAC by 35% and increase ROAS from 2.1x to 4.5x in 60 days",
        },
        "full_funnel_growth_suite": {
            "brand_name": "GrowthStack",
            "industry": "B2B SaaS - Marketing Automation",
            "value_prop": "All-in-one marketing automation platform for mid-market companies",
            "goal": "Scale from $2M to $10M ARR through full-funnel optimization in 12 months",
        },
    }

    ctx = pack_contexts.get(pack_name, pack_contexts["launch_gtm_pack"])

    brand = BrandBrief(
        brand_name=ctx["brand_name"],
        industry=ctx["industry"],
        geography="North America",
        website_url=f"https://{ctx['brand_name'].lower()}.com",
        value_proposition=ctx["value_prop"],
        target_persona_label="Decision makers and influencers in target market",
        voice_notes="Professional, strategic, results-driven, data-backed",
    )

    goal = GoalBrief(
        primary_goal=ctx["goal"],
        timeline="90 days",
        kpis=["Metric 1", "Metric 2", "Metric 3"],
        secondary_goals=["Support goal 1", "Support goal 2"],
        success_criteria="Achieve primary goal with measurable impact",
    )

    return GenerateRequest(
        brief=type("Brief", (), {"brand": brand, "goal": goal})(),
        wow_enabled=True,
        wow_package_key=pack_name,
    )


def test_pack(pack_name: str) -> Dict:
    """Test single pack and return results."""
    print("\n" + "=" * 80)
    print(f"TESTING: {pack_name.upper()}")
    print("=" * 80)

    req = create_test_brief(pack_name)

    try:
        # Generate pack
        output = aicmo_generate(req)
        full_markdown = output.wow_markdown or output.full_report

        if not full_markdown:
            return {
                "pack": pack_name,
                "status": "GENERATION_FAILED",
                "error": "No markdown generated",
            }

        print(f"✓ Generated {len(full_markdown):,} characters")

        # Parse sections
        sections = parse_wow_markdown_to_sections(full_markdown)
        print(f"✓ Parsed {len(sections)} sections")

        # Validate
        result = validate_report_sections(pack_key=pack_name, sections=sections, brief=req.brief)

        # Count issues
        error_count = 0
        warning_count = 0
        section_details = []

        for section_result in result.section_results:
            errors = [issue for issue in section_result.issues if issue.severity == "error"]
            warnings = [issue for issue in section_result.issues if issue.severity == "warning"]

            error_count += len(errors)
            warning_count += len(warnings)

            if errors or warnings:
                section_details.append(
                    {
                        "section_id": section_result.section_id,
                        "errors": [{" code": e.code, "message": e.message} for e in errors],
                        "warnings": [{"code": w.code, "message": w.message} for w in warnings],
                    }
                )

        return {
            "pack": pack_name,
            "status": result.status,
            "total_sections": len(sections),
            "error_count": error_count,
            "warning_count": warning_count,
            "section_issues": section_details,
        }

    except Exception as e:
        import traceback

        return {
            "pack": pack_name,
            "status": "EXCEPTION",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


def main():
    """Run validation on all packs."""
    packs_to_test = [
        "launch_gtm_pack",
        "brand_turnaround_lab",
        "retention_crm_booster",
        "performance_audit_revamp",
        "full_funnel_growth_suite",
    ]

    print("\n" + "=" * 80)
    print("AICMO PACK HARDENING - COMPREHENSIVE VALIDATION")
    print("=" * 80)
    print(f"Testing {len(packs_to_test)} packs")
    print("Reference standard: strategy_campaign_standard (0 errors, 2 warnings)")
    print("=" * 80)

    all_results = []

    for pack_name in packs_to_test:
        result = test_pack(pack_name)
        all_results.append(result)

        # Print immediate summary
        if result["status"] == "PASS" or result["status"] == "PASS_WITH_WARNINGS":
            status_icon = "✅"
        else:
            status_icon = "❌"

        print(
            f"\n{status_icon} {pack_name}: {result.get('error_count', '?')} errors, {result.get('warning_count', '?')} warnings"
        )

        # Print section-level issues
        if result.get("section_issues"):
            for section in result["section_issues"][:5]:  # Show first 5
                print(f"   [{section['section_id']}]")
                for error in section.get("errors", [])[:2]:
                    print(f"      ❌ {error['code']}")

    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    total_errors = sum(r.get("error_count", 0) for r in all_results)
    total_warnings = sum(r.get("warning_count", 0) for r in all_results)

    print(f"Total Errors: {total_errors}")
    print(f"Total Warnings: {total_warnings}")
    print()

    for result in all_results:
        pack = result["pack"]
        status = result.get("status", "UNKNOWN")
        errors = result.get("error_count", "?")
        warnings = result.get("warning_count", "?")

        if status in ["PASS", "PASS_WITH_WARNINGS"]:
            icon = "✅"
        else:
            icon = "❌"

        print(f"{icon} {pack:35} | {errors:3} errors | {warnings:3} warnings")

    print("\n" + "=" * 80)

    if total_errors == 0:
        print("✅ ALL PACKS PASS - READY FOR CLIENT DELIVERY")
        return 0
    else:
        print(f"❌ {total_errors} TOTAL ERRORS - FIXES REQUIRED")
        print("\nNext steps:")
        print("1. Run individual pack tests for detailed error analysis")
        print("2. Fix generators section by section")
        print("3. Re-run this script until 0 errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())
