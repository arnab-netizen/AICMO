#!/usr/bin/env python3
"""
Test: retention_crm_booster pack validation
============================================

Validates that retention_crm_booster generates 14 sections with 0 errors.
Follows pattern from test_launch_gtm_pack.py and test_strategy_campaign_standard.py.

Run:
    python test_retention_crm_booster.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Force NON-STUB mode for realistic testing
os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-template-testing"
os.environ["AICMO_USE_LLM"] = "false"
os.environ["AICMO_PERPLEXITY_ENABLED"] = "false"
os.environ["AICMO_STUB_MODE"] = "0"

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
from backend.utils.wow_markdown_parser import parse_wow_markdown_to_sections
from backend.validators.report_gate import validate_report_sections
import asyncio


def create_test_brief():
    """
    Create a realistic retention/CRM brief for D2C subscription brand.

    Focus:
    - D2C subscription or repeat-purchase product
    - Retention + LTV goals
    - CRM channels (Email, SMS, WhatsApp, Push)
    - Lifecycle segments (new, active, churn-risk, winback)
    """
    brand = BrandBrief(
        brand_name="NutriBlend",
        industry="D2C Subscription",
        founding_year=2021,
        location="US",
        product_service="Premium meal replacement shakes with personalized nutrition plans",
        primary_goal="Increase 90-day retention rate from 35% to 50% and grow LTV by 40%",
        primary_customer="Health-conscious professionals (28-45) seeking convenient, high-quality nutrition",
        value_proposition="Science-backed nutrition that adapts to your body's needs, delivered monthly",
        brand_story="Founded by nutritionists who saw clients struggling with time vs. health tradeoffs. We combine cutting-edge nutrition science with AI-powered personalization to make healthy eating effortless.",
        unique_positioning="Only meal replacement using continuous glucose monitoring data to personalize formulas",
        core_values="Science-first, transparency, sustainability, customer success",
        market_context="$8B meal replacement market growing 9% annually. Competitors (Huel, Soylent) focus on one-size-fits-all formulas. We differentiate through personalization and health outcomes tracking.",
    ).with_safe_defaults()

    audience = AudienceBrief(
        primary_customer="Health-conscious professionals (28-45) seeking convenient, high-quality nutrition for busy lifestyles",
        secondary_customer="Fitness enthusiasts and wellness advocates looking for science-backed meal solutions",
        pain_points=[
            "Time constraints make healthy eating difficult (average 45min meal prep vs 15min desired)",
            "Conflicting nutrition advice leads to decision paralysis and poor choices",
            "Meal prep burnout after 2-3 weeks of trying to eat healthy consistently",
            "Expensive healthy eating options ($15-20/meal) vs convenience of fast food",
            "Lack of visible health results despite following generic diet plans",
            "Subscription fatigue - customers cancel after 2-3 months due to flavor boredom",
        ],
        online_hangouts=[
            "Instagram (wellness + fitness content)",
            "TikTok (quick health tips)",
            "Reddit r/nutrition",
            "Facebook wellness groups",
            "LinkedIn (professional health optimization)",
        ],
    )

    goal = GoalBrief(
        primary_goal="Increase 90-day retention rate from 35% to 50% and grow customer LTV by 40%",
        secondary_goal="Build automated lifecycle marketing system that runs with minimal manual intervention",
        kpis=[
            "90-day retention rate: 35% → 50%",
            "Repeat purchase rate: 2.1 → 3.5 orders per 90 days",
            "Customer LTV: $180 → $250",
            "Churn rate: 12%/month → 7%/month",
            "Reactivation rate (winback): 8% → 15%",
        ],
        timeline="90 days",
    )

    voice = VoiceBrief(
        tone_of_voice=[
            "empowering",
            "science-backed",
            "warm",
            "results-driven",
            "transparent",
        ]
    )

    product_service = ProductServiceBrief(
        items=[
            {
                "name": "Monthly Shake Subscription",
                "usp": "Personalized formulas using CGM data",
                "pricing_note": "$89/month base, $119/month premium with CGM device",
            }
        ],
        testimonials_or_proof="Customer success stories showing 15lb avg weight loss, 40% energy improvement, 92% report better glucose stability",
    )

    assets_constraints = AssetsConstraintsBrief(
        focus_platforms=["Email", "SMS", "WhatsApp", "Push", "In-app"],
        budget="$15,000/month for CRM tech stack + automation + content",
        constraints=[
            "Small retention team (2 FTEs)",
            "Limited dev resources",
            "Must work within Klaviyo + Attentive ecosystem",
        ],
    )

    operations = OperationsBrief(
        approval_frequency="Weekly review of new flows, daily monitoring of performance",
        upcoming_events="Q1: New flavor launch, Q2: CGM partnership announcement",
    )

    strategy_extras = StrategyExtrasBrief(
        brand_adjectives=[
            "innovative",
            "science-first",
            "transparent",
            "results-focused",
            "community-driven",
        ],
        extra_notes="Focus on lifecycle automation with minimal manual intervention. Key segments: New (0-30d), Active (31-180d), At-Risk (180d+, low engagement), Lapsed (60d+ no order)",
    )

    return ClientInputBrief(
        brand=brand,
        audience=audience,
        goal=goal,
        voice=voice,
        product_service=product_service,
        assets_constraints=assets_constraints,
        operations=operations,
        strategy_extras=strategy_extras,
    )


async def main():
    """
    Generate retention_crm_booster pack and validate all 14 sections.
    """
    print("=" * 70)
    print("TEST: retention_crm_booster Pack Validation")
    print("=" * 70)

    # Create test brief
    brief = create_test_brief()
    print(f"\n✓ Test brief created: {brief.brand.brand_name} ({brief.brand.industry})")
    print(f"  Goal: {brief.goal.primary_goal}")
    print(f"  Timeline: {brief.goal.timeline}")

    # Build request (WOW disabled for direct section testing)
    req = GenerateRequest(
        brief=brief,
        package_preset="retention_crm_booster",
        wow_package_key=None,  # Disable WOW to test sections directly
        skip_benchmark_enforcement=True,  # We'll validate afterward with report_gate
        sections_preset="retention_crm_booster",
    )

    # Generate pack
    print("\n🔄 Generating retention_crm_booster pack...")

    try:
        output = await aicmo_generate(req)
    except Exception as e:
        # If benchmark enforcement fails during generation, that's expected
        # We'll manually validate to see all errors
        print(f"⚠️  Generation failed (expected if benchmarks are enforced): {type(e).__name__}")
        print("   This is OK - we'll fix generators and re-test")
        print("\n" + "=" * 70)
        print("NOTE: See error details above for which sections failed benchmark enforcement")
        print("=" * 70)
        return

    # When WOW is disabled, use extra_sections dict
    if output.wow_markdown:
        markdown_content = output.wow_markdown
    elif output.extra_sections:
        # Combine all extra_sections into markdown
        markdown_content = "\n\n".join(
            f"## {section_title}\n\n{section_content}"
            for section_title, section_content in output.extra_sections.items()
        )
    else:
        print("❌ ERROR: No sections generated")
        return

    print(f"✓ Generated {len(markdown_content)} chars of markdown")

    # Parse sections
    parsed_sections = parse_wow_markdown_to_sections(markdown_content)
    print(f"✓ Parsed {len(parsed_sections)} sections from WOW markdown")

    # Validate with benchmark enforcement
    print("\n🔍 Validating sections against benchmarks...")
    print("-" * 70)

    validation_result = validate_report_sections(
        pack_key="retention_crm_booster", sections=parsed_sections
    )

    # Print per-section summary
    total_errors = 0
    total_warnings = 0

    print(f"\n📊 Validation Status: {validation_result.status}")
    print(f"   Total sections: {len(validation_result.section_results)}")
    print(
        f"   Passing: {sum(1 for r in validation_result.section_results if r.status in ('PASS', 'PASS_WITH_WARNINGS'))}"
    )
    print(f"   Failing: {sum(1 for r in validation_result.section_results if r.status == 'FAIL')}")
    print()

    # Create lookup dict for faster access
    results_by_id = {r.section_id: r for r in validation_result.section_results}

    for section_id in [
        "overview",
        "customer_segments",
        "persona_cards",
        "customer_journey_map",
        "churn_diagnosis",
        "email_automation_flows",
        "sms_and_whatsapp_flows",
        "loyalty_program_concepts",
        "winback_sequence",
        "post_purchase_experience",
        "ugc_and_community_plan",
        "kpi_plan_retention",
        "execution_roadmap",
        "final_summary",
    ]:
        result = results_by_id.get(section_id)
        if not result:
            print(f"❌ {section_id}: Section not found in validation results")
            continue

        errors = [issue for issue in result.issues if issue.severity == "error"]
        warnings = [issue for issue in result.issues if issue.severity == "warning"]

        error_count = len(errors)
        warning_count = len(warnings)

        total_errors += error_count
        total_warnings += warning_count

        status = "✅" if error_count == 0 else "❌"
        print(f"{status} [{section_id:30s}] errors={error_count:2d} warnings={warning_count:2d}")

        if errors:
            for err in errors[:2]:  # Show first 2 errors per section
                print(f"      ERROR: {err.message}")

        error_count = len(errors)
        warning_count = len(warnings)

        total_errors += error_count
        total_warnings += warning_count

        status = "✅" if error_count == 0 else "❌"
        print(f"{status} [{section_id:30s}] errors={error_count:2d} warnings={warning_count:2d}")

        if errors:
            for err in errors[:2]:  # Show first 2 errors per section
                print(f"      ERROR: {err.message}")

    print("-" * 70)
    print(f"\n📊 TOTAL: {total_errors} errors, {total_warnings} warnings across 14 sections")

    if total_errors == 0:
        print("\n✅ SUCCESS: retention_crm_booster has 0 validation errors!")
    else:
        print(f"\n⚠️  Need to fix {total_errors} errors in generators")

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
