#!/usr/bin/env python3
"""
Development validation script for launch_gtm_pack.

Proves that the pack:
1. Generates all 13 required sections
2. Passes WOW template application
3. Passes benchmark validation with 0 errors
4. Has all subsections correctly merged into parent sections

Usage:
    python scripts/dev_validate_launch_gtm_pack.py
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
    """Create a realistic synthetic brief for launch testing."""
    brand = BrandBrief(
        brand_name="LaunchTest Platform",
        industry="D2C - Consumer Tech",
        geography="United States (Austin, TX)",
        product_service="AI-powered product launch management platform for DTC brands",
        value_proposition="Execute flawless launches with automated workflows, market intelligence, and real-time analytics achieving 3x higher success rates",
        primary_goal="Launch platform 2.0 and acquire 1,000 paying customers in 90 days",
        primary_customer="Marketing Directors and Brand Managers at mid-market DTC brands ($5M-$50M revenue)",
    ).with_safe_defaults()

    audience = AudienceBrief(
        primary_customer="Marketing Directors, Brand Managers, Product Leads at DTC consumer brands with $5M-$50M ARR",
        secondary_customer="E-commerce Managers, Growth Marketers at emerging consumer brands",
        audience_size_estimate="50K addressable market in US",
        demographics="28-45 years old, 55% female, marketing/product leaders, based in major tech hubs",
        psychographics="Data-driven, launch-obsessed, results-focused, values automation and insights",
        pain_points=[
            "Launch coordination failures across marketing, sales, product teams",
            "Manual spreadsheet management causing missed deadlines and budget overruns",
            "No centralized platform for launch metrics and market response tracking",
            "Competitive intelligence gathering takes 20+ hours per launch",
            "Static launch playbooks that teams ignore or can't adapt",
        ],
        online_behavior="Active on LinkedIn, Instagram, Twitter/X, Product Hunt, Reddit r/startups",
        online_hangouts=["LinkedIn", "Instagram", "Twitter/X", "Reddit r/startups", "Product Hunt"],
    )

    goal = GoalBrief(
        primary_goal="Launch platform 2.0 and acquire 1,000 paying customers ($99/month tier) generating $100K MRR within 90 days",
        secondary_goals="Build 10,000 pre-launch waitlist, achieve Product Hunt #1 Product of Day, generate $100K MRR by day 90",
        timeline="90 days (January-March 2025)",
        kpis=[
            "1,000 paid customers ($99/month tier)",
            "$100K monthly recurring revenue by day 90",
            "10,000 pre-launch waitlist signups",
            "Product Hunt #1 Product of the Day on launch day",
            "4.5+ G2 rating from first 100 customers",
        ],
        success_metrics="1,000 paid customers, $100K MRR, Product Hunt #1, 4.5+ G2 rating, 60% trial activation rate",
    )

    voice = VoiceBrief(
        brand_voice="Bold, innovative, data-driven, startup-friendly, results-focused",
        tone_adjectives="Innovative, data-driven, launch-obsessed, results-focused, agile",
        messaging_pillars="Launch success through automation, data-driven insights, proven playbooks, community learning",
        key_differentiators="AI-powered automation, real-time market intelligence, 3x higher launch success rates",
        tone_of_voice=["bold", "innovative", "data-driven", "startup-friendly"],
    )

    product = ProductServiceBrief(
        core_offerings="AI launch platform with workflow automation, competitive intelligence, analytics, launch playbooks",
        price_points="$99/month professional tier, $299/month team tier, 14-day free trial",
        unique_selling_propositions="Automated launch workflows, real-time market intelligence, proven 3x success rate improvement",
        competitive_advantages="AI-powered insights, comprehensive launch management, active community of successful launchers",
    )

    assets = AssetsConstraintsBrief(
        existing_assets="Brand guidelines, product screenshots, beta customer testimonials, launch playbooks",
        constraints=[
            "Limited video production budget ($5K)",
            "No paid influencer budget",
            "Must maintain startup brand authenticity",
        ],
        brand_guidelines="Bold, modern design; startup-friendly aesthetic; authentic photography over stock images",
        focus_platforms=[
            "Instagram (launch stories + Reels)",
            "LinkedIn (B2B thought leadership)",
            "Product Hunt (launch day)",
            "Twitter/X (real-time launch updates)",
            "Email (nurture sequences)",
        ],
    )

    operations = OperationsBrief(
        team_structure="3-person marketing team, founder involvement in PR, community management outsourced",
        approval_workflow="CMO approval for paid ads, founder approval for PR and partnerships",
        budget_constraints="$35K total launch budget ($25K paid ads, $5K video, $5K partnerships)",
        existing_campaigns="Building pre-launch waitlist via LinkedIn ads, partner email swaps",
    )

    strategy_extras = StrategyExtrasBrief(
        campaign_name="LaunchBox 2.0 Launch Campaign",
        inspiration_brands="Product Hunt, Notion, Figma, Linear (successful product launches)",
        must_avoid="Overpromising, hype without substance, generic marketing speak, fake urgency",
        key_partnerships="Integrations with Shopify, Stripe, HubSpot; partnerships with DTC communities",
        seasonal_considerations="Q1 launch timing aligned with New Year planning cycles",
        brand_adjectives=[
            "innovative",
            "data-driven",
            "launch-obsessed",
            "results-focused",
            "agile",
        ],
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
    print("LAUNCH_GTM_PACK - VALIDATION PROOF")
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
        package_preset="launch_gtm_pack",
        wow_package_key="launch_gtm_pack",
        wow_enabled=True,
        use_learning=False,
        is_regeneration=False,
        skip_benchmark_enforcement=True,
    )

    try:
        output = await aicmo_generate(req)
        print(f"   ✅ Generated {len(output.wow_markdown):,} characters")
        print(f"   ✅ WOW markdown includes {output.wow_markdown.count('##')} total headings")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False
    print()

    # Step 3: Parse to sections
    print("3️⃣  Parsing WOW markdown to sections...")
    try:
        parsed_sections = parse_wow_markdown_to_sections(output.wow_markdown)
        print(f"   ✅ Parsed {len(parsed_sections)} total sections (including subsections)")

        section_ids = [s["id"] for s in parsed_sections]
        unique_ids = set(section_ids)
        print(f"   ✅ Unique section IDs: {len(unique_ids)}")
        print(f"   ✅ First 13 section IDs: {section_ids[:13]}")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False
    print()

    # Step 4: Validate with section merging
    print("4️⃣  Running benchmark validation (with subsection merging)...")
    try:
        result = validate_report_sections(pack_key="launch_gtm_pack", sections=parsed_sections)

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
    if errors == 0 and len(validated_ids) == 13:
        print("✅ PROOF COMPLETE: launch_gtm_pack PASSES ALL CHECKS")
        print()
        print(f"   • All 13 canonical sections generated: {validated_ids}")
        print(f"   • All sections pass benchmark validation: 0 errors, {warnings} warnings")
        print(
            f"   • Subsection merging works correctly: {len(parsed_sections)} → {len(validated_ids)}"
        )
        print("=" * 80)
        return True
    else:
        print("❌ PROOF FAILED: Issues detected")
        print()
        print(f"   • Expected 13 sections, got {len(validated_ids)}")
        print(f"   • Errors: {errors}")
        print("=" * 80)
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
