#!/usr/bin/env python3
"""
Development validation script for strategy_campaign_standard pack.

Proves that the pack:
1. Generates all 17 required sections
2. Passes WOW template application
3. Passes benchmark validation with no errors
4. Has all subsections correctly merged into parent sections

Usage:
    python scripts/dev_validate_strategy_campaign_standard.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Force template-only mode (no LLM calls)
os.environ["OPENAI_API_KEY"] = "sk-test-fake-key"
os.environ["AICMO_USE_LLM"] = "false"
os.environ["AICMO_PERPLEXITY_ENABLED"] = "false"
os.environ["AICMO_STUB_MODE"] = "0"

import asyncio
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


def create_synthetic_brief() -> ClientInputBrief:
    """Create a realistic synthetic brief for testing."""
    brand = BrandBrief(
        brand_name="Test Strategy Brand",
        industry="Health & Wellness",
        geography="US & UK",
        product_service="subscription-based wellness app with AI coaching",
        value_proposition="Personalized wellness journeys powered by AI, delivering measurable health outcomes in 30 days",
        primary_goal="Acquire 10,000 paying subscribers and increase LTV through engagement",
        primary_customer="Health-conscious professionals aged 28-45 seeking sustainable lifestyle changes",
    )

    audience = AudienceBrief(
        primary_customer="Busy professionals, health enthusiasts, people recovering from lifestyle-related conditions",
        audience_size_estimate="2.5M addressable market in US/UK",
        demographics="28-45 years old, 60% female, household income $75K+, urban/suburban",
        psychographics="Values convenience, science-backed solutions, community support, measurable results",
        pain_points=[
            "Lack of time",
            "Conflicting health advice",
            "Difficulty maintaining motivation",
            "Plateau frustration",
        ],
        online_behavior="Active on Instagram/LinkedIn, reads health blogs, listens to wellness podcasts",
    )

    goal = GoalBrief(
        primary_goal="Increase qualified free trial signups by 40% within 90 days",
        secondary_goals="Reduce churn by 15%, increase app engagement to 4+ sessions/week",
        timeline="90-day campaign with ongoing optimization",
        kpis=[
            "Free trial signups",
            "Conversion to paid",
            "Retention rate",
            "Session frequency",
            "NPS score",
        ],
        success_metrics="10K paid subscribers, $50 CPA, 70% trial-to-paid conversion, <5% monthly churn",
    )

    voice = VoiceBrief(
        brand_voice="Supportive, evidence-based, empowering without being preachy",
        tone_adjectives="Encouraging, authentic, science-backed, friendly, aspirational",
        messaging_pillars="Progress over perfection, science-backed results, community support, sustainable change",
        key_differentiators="AI-powered personalization, 30-day proven results, holistic approach",
    )

    product = ProductServiceBrief(
        core_offerings="AI wellness app with meal planning, fitness tracking, mindfulness coaching, sleep optimization",
        price_points="$29.99/month, $199/year (33% savings), 14-day free trial",
        unique_selling_propositions="Personalized AI coach, integrated approach (nutrition + fitness + mental health), measurable outcomes",
        competitive_advantages="Advanced AI personalization engine, clinically validated protocols, active community of 50K+ members",
    )

    assets = AssetsConstraintsBrief(
        existing_assets="Brand guidelines, app screenshots, user testimonials, clinical study results",
        constraints=[
            "Limited video production budget",
            "No celebrity endorsements",
            "HIPAA-compliant content only",
        ],
        brand_guidelines="Clean, modern design; teal and coral colors; sans-serif fonts; lifestyle photography",
    )

    operations = OperationsBrief(
        team_structure="2-person marketing team, outsourced content creation, in-house community management",
        approval_workflow="CMO approval required for paid ads and partnerships",
        budget_constraints="$50K total budget for 90-day campaign ($35K paid ads, $15K content/creative)",
        existing_campaigns="Running Google Ads (paused for optimization), email nurture sequences to 15K leads",
    )

    strategy_extras = StrategyExtrasBrief(
        inspiration_brands="Calm, Noom, Headspace, Peloton",
        must_avoid="Weight loss claims, before/after photos, medical advice, miracle cure language",
        key_partnerships="Integration with Fitbit/Apple Watch, collaboration with registered dietitians",
        seasonal_considerations="New Year resolution timing (Jan), summer fitness focus (May-Jul)",
    )

    return ClientInputBrief(
        brand=brand,
        audience=audience,
        goal=goal,
        voice=voice,
        product_service=product,
        assets_constraints=assets,
        operations=operations,
        strategy_extras=strategy_extras,
    )


async def main():
    """Run validation proof."""
    print("=" * 80)
    print("STRATEGY_CAMPAIGN_STANDARD PACK - VALIDATION PROOF")
    print("=" * 80)
    print()

    # Step 1: Create brief
    print("1️⃣  Creating synthetic test brief...")
    brief = create_synthetic_brief()
    print(f"   ✅ Brand: {brief.brand.brand_name}")
    print(f"   ✅ Industry: {brief.brand.industry}")
    print(f"   ✅ Goal: {brief.goal.primary_goal}")
    print()

    # Step 2: Generate report
    print("2️⃣  Generating full WOW report...")
    req = GenerateRequest(
        brief=brief,
        package_preset="strategy_campaign_standard",  # Triggers section generation
        wow_package_key="strategy_campaign_standard",  # Applies WOW template
        wow_enabled=True,
        use_learning=False,
        is_regeneration=False,
        skip_benchmark_enforcement=True,  # Get output even with validation warnings
    )

    try:
        output = await aicmo_generate(req)
        print(f"   ✅ Generated {len(output.wow_markdown)} characters")
        print(f"   ✅ WOW markdown includes {output.wow_markdown.count('##')} total headings")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False
    print()

    # Step 3: Parse to sections
    print("3️⃣  Parsing WOW markdown to sections...")
    try:
        parsed_sections = parse_wow_markdown_to_sections(output.wow_markdown)
        print(f"   ✅ Parsed {len(parsed_sections)} total sections (including subsections)")

        # Show breakdown
        section_ids = [s["id"] for s in parsed_sections]
        unique_ids = set(section_ids)
        print(f"   ✅ Unique section IDs: {len(unique_ids)}")
        print(f"   ✅ First 10 section IDs: {section_ids[:10]}")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False
    print()

    # Step 4: Validate with section merging
    print("4️⃣  Running benchmark validation (with subsection merging)...")
    try:
        result = validate_report_sections(
            pack_key="strategy_campaign_standard", sections=parsed_sections
        )

        print(f"   Status: {result.status}")
        print(f"   Canonical sections validated: {len(result.section_results)}")
        print()

        # Count issues by severity
        errors = sum(
            1 for sec in result.section_results for issue in sec.issues if issue.severity == "error"
        )
        warnings = sum(
            1
            for sec in result.section_results
            for issue in sec.issues
            if issue.severity == "warning"
        )

        print(f"   Errors: {errors}")
        print(f"   Warnings: {warnings}")
        print()

        # Show section IDs that were validated
        validated_ids = [sec.section_id for sec in result.section_results]
        print(f"   Validated section IDs: {validated_ids}")
        print()

        # Show any errors
        if errors > 0:
            print("   ❌ ERRORS FOUND:")
            for sec in result.section_results:
                for issue in sec.issues:
                    if issue.severity == "error":
                        print(f"      [{sec.section_id}] {issue.code}: {issue.message}")
            print()

        # Show warnings (if reasonable number)
        if 0 < warnings <= 15:
            print("   ⚠️  WARNINGS (non-blocking):")
            for sec in result.section_results:
                for issue in sec.issues:
                    if issue.severity == "warning":
                        print(f"      [{sec.section_id}] {issue.code}: {issue.message}")
            print()

    except Exception as e:
        print(f"   ❌ VALIDATION FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Step 5: Final verdict
    print("=" * 80)
    if errors == 0 and len(validated_ids) == 17:
        print("✅ PROOF COMPLETE: strategy_campaign_standard PASSES ALL CHECKS")
        print()
        print(f"   • All 17 canonical sections generated: {validated_ids}")
        print(f"   • All sections pass benchmark validation: 0 errors, {warnings} warnings")
        print(
            f"   • Subsection merging works correctly: {len(parsed_sections)} → {len(validated_ids)}"
        )
        print("=" * 80)
        return True
    else:
        print("❌ PROOF FAILED: Issues detected")
        print()
        print(f"   • Expected 17 sections, got {len(validated_ids)}")
        print(f"   • Errors: {errors}")
        print("=" * 80)
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
