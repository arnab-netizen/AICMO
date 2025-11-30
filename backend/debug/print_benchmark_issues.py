#!/usr/bin/env python3
"""
Debug helper to inspect benchmark validation issues for any pack.

Usage:
    python -m backend.debug.print_benchmark_issues quick_social_basic
    python -m backend.debug.print_benchmark_issues strategy_campaign_standard
    python -m backend.debug.print_benchmark_issues full_funnel_growth_suite

This is a DEV-ONLY tool for debugging generator/benchmark mismatches.
NOT used in production runtime.
"""
import sys
import argparse

from backend.validators.report_gate import validate_report_sections


def get_default_brief():
    """Create a realistic default brief for testing."""
    # Import here to avoid module-level import issues
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

    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="Test Brand Co",
            industry="Technology",
            product_service="SaaS platform for team collaboration",
            primary_goal="Increase monthly active users by 40%",
            primary_customer="Remote team leads and project managers",
            secondary_customer="Tech-savvy individual contributors",
            brand_tone="professional, friendly, innovative",
            location="San Francisco, CA",
            timeline="Q1 2026 (90 days)",
        ),
        audience=AudienceBrief(
            primary_customer="Remote team leads and project managers",
            secondary_customer="Tech-savvy individual contributors",
            pain_points=["Time constraints", "Tool overload"],
            online_hangouts=["LinkedIn", "X"],
        ),
        goal=GoalBrief(
            primary_goal="Increase monthly active users by 40%",
            secondary_goal="Improve customer retention",
            timeline="3 months",
            kpis=["MAU", "Retention Rate", "Trial Signups"],
        ),
        voice=VoiceBrief(
            tone_of_voice=["professional", "friendly", "innovative"],
        ),
        product_service=ProductServiceBrief(
            current_offers="Team collaboration platform",
            testimonials_or_proof="4.5/5 stars from 500+ teams",
        ),
        assets_constraints=AssetsConstraintsBrief(
            focus_platforms=["LinkedIn", "X", "Instagram"],
        ),
        operations=OperationsBrief(
            needs_calendar=True,
        ),
        strategy_extras=StrategyExtrasBrief(
            brand_adjectives=["innovative", "reliable", "user-friendly"],
            success_30_days="30% increase in trial signups",
            tagline="Work together, anywhere",
        ),
    )


def print_pack_benchmark_issues(pack_key: str, brief) -> int:
    """
    Generate sections for a pack and print detailed benchmark validation issues.

    Args:
        pack_key: Pack key to test (e.g., "quick_social_basic")
        brief: Client brief to use for generation

    Returns:
        0 if all sections pass, 1 if any sections fail
    """
    from backend.main import (
        PACKAGE_PRESETS,
        GenerateRequest,
        SECTION_GENERATORS,
    )
    from backend.main import (
        MarketingPlanView,
        CampaignBlueprintView,
        SocialCalendarView,
        MessagingPyramid,
        CampaignObjectiveView,
        AudiencePersonaView,
    )
    from datetime import date, timedelta

    # Validate pack exists
    if pack_key not in PACKAGE_PRESETS:
        print(f"❌ ERROR: Unknown pack key '{pack_key}'")
        print("\nAvailable packs:")
        for pk in sorted(PACKAGE_PRESETS.keys()):
            print(f"  - {pk}")
        return 1

    print("=" * 80)
    print(f"BENCHMARK VALIDATION DEBUG: {pack_key}")
    print("=" * 80)
    print()

    # Create request
    req = GenerateRequest(
        brief=brief,
        wow_package_key=pack_key,
    )

    try:
        # Get section IDs for this pack
        pack_config = PACKAGE_PRESETS[pack_key]
        section_ids = pack_config["sections"]
        print(f"📋 Pack sections: {len(section_ids)} sections")
        print(f"   {', '.join(section_ids[:5])}{'...' if len(section_ids) > 5 else ''}\n")

        # Create minimal components needed by generators
        print("🔄 Creating components...")

        b = brief.brand
        g = brief.goal
        a = brief.audience
        today = date.today()

        # Minimal MarketingPlanView
        mp = MarketingPlanView(
            executive_summary=f"{b.brand_name} marketing plan for {g.primary_goal}",
            situation_analysis="Situation analysis",
            strategy="Core strategy",
            pillars=[
                {"name": "Pillar 1", "description": "Description 1"},
                {"name": "Pillar 2", "description": "Description 2"},
                {"name": "Pillar 3", "description": "Description 3"},
            ],
            messaging_pyramid=MessagingPyramid(
                promise=f"{b.brand_name} delivers quality solutions",
                key_messages=["Message 1", "Message 2", "Message 3"],
                proof_points=["Proof 1", "Proof 2"],
                values=["Value 1", "Value 2"],
            ),
        )

        # Minimal CampaignBlueprintView
        cb = CampaignBlueprintView(
            big_idea=f"Make {b.brand_name} the default choice",
            objective=CampaignObjectiveView(
                primary=g.primary_goal or "growth",
                secondary=g.secondary_goal,
            ),
            audience_persona=AudiencePersonaView(
                name="Core Buyer",
                description=f"{a.primary_customer} seeking solutions",
            ),
        )

        # Minimal SocialCalendarView
        cal = SocialCalendarView(
            start_date=today,
            end_date=today + timedelta(days=6),
            posts=[],
        )

        print("✅ Components ready\n")

        # Generate all sections for this pack
        print("🔄 Generating sections...")

        # Generate sections WITHOUT enforcement to see raw issues
        results = {}
        context = {
            "req": req,
            "mp": mp,
            "cb": cb,
            "cal": cal,
            "pr": None,
            "creatives": None,
            "action_plan": None,
        }

        for section_id in section_ids:
            generator_fn = SECTION_GENERATORS.get(section_id)
            if generator_fn:
                try:
                    results[section_id] = generator_fn(**context)
                except Exception as e:
                    print(f"   ⚠️  Generator failed for '{section_id}': {e}")
                    results[section_id] = ""

        sections_dict = results
        print(f"✅ Generated {len(sections_dict)} sections\n")

        # Build sections list for validation
        sections_list = [
            {"id": section_id, "content": content}
            for section_id, content in sections_dict.items()
            if content  # Skip empty sections
        ]

        if not sections_list:
            print("⚠️  WARNING: No sections generated!")
            return 1

        # Validate against benchmarks
        print("🔍 Validating against benchmarks...")
        result = validate_report_sections(pack_key=pack_key, sections=sections_list)

        print()
        print("=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Status:           {result.status}")
        print(f"Total Sections:   {len(result.section_results)}")
        print(f"Passing Sections: {sum(1 for r in result.section_results if r.status == 'PASS')}")
        print(f"Failing Sections: {len(result.failing_sections())}")
        print()

        if len(result.failing_sections()) == 0:
            print("✅ ALL SECTIONS PASSED BENCHMARK VALIDATION!")
            return 0

        # Print detailed failures
        print("=" * 80)
        print(f"DETAILED FAILURES ({result.failing_sections} sections)")
        print("=" * 80)
        print()

        for section_result in result.section_results:
            if section_result.issues:
                section_id = section_result.section_id
                content = sections_dict.get(section_id, "")

                # Calculate metrics
                word_count = len(content.split())
                lines = content.split("\n")
                line_count = len([line for line in lines if line.strip()])
                heading_lines = [line for line in lines if line.strip().startswith("#")]
                heading_count = len(heading_lines)
                bullet_count = len(
                    [line for line in lines if line.strip().startswith(("-", "*", "+"))]
                )

                print(f"❌ Section: {section_id}")
                print(f"   Status: {section_result.status}")
                print("   Actual Metrics:")
                print(f"     - Words: {word_count}")
                print(f"     - Headings: {heading_count}")
                print(f"     - Bullets: {bullet_count}")
                print(f"     - Lines: {line_count}")

                if heading_lines:
                    print("   Found Headings:")
                    for h in heading_lines[:5]:  # Show first 5
                        print(f"     - {h.strip()}")

                print("   Issues:")
                for issue in section_result.issues:
                    severity = issue.severity.upper() if issue.severity else "ERROR"
                    print(f"     [{severity}] {issue.code}: {issue.message}")

                # Show content preview
                print("   Content Preview (first 400 chars):")
                preview_lines = []
                char_count = 0
                for line in lines:
                    if char_count >= 400:
                        break
                    preview_lines.append(f"     {line}")
                    char_count += len(line) + 1
                print("\n".join(preview_lines))
                print("     ...")
                print()

        return 1

    except Exception as e:
        print("\n❌ ERROR during generation/validation:")
        print(f"{e}")
        import traceback

        traceback.print_exc()
        return 1


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Debug benchmark validation issues for AICMO packs"
    )
    parser.add_argument(
        "pack_key",
        nargs="?",
        default="quick_social_basic",
        help="Pack key to test (default: quick_social_basic)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Test all packs sequentially",
    )

    args = parser.parse_args()

    if args.all:
        from backend.main import PACKAGE_PRESETS

        print("Testing all packs...")
        print()

        results = {}
        for pack_key in sorted(PACKAGE_PRESETS.keys()):
            brief = get_default_brief()
            exit_code = print_pack_benchmark_issues(pack_key, brief)
            results[pack_key] = exit_code
            print("\n")

        # Summary
        print("=" * 80)
        print("ALL PACKS SUMMARY")
        print("=" * 80)
        passing = [pk for pk, code in results.items() if code == 0]
        failing = [pk for pk, code in results.items() if code != 0]

        print(f"✅ Passing: {len(passing)}/{len(results)}")
        for pk in passing:
            print(f"   - {pk}")

        if failing:
            print(f"\n❌ Failing: {len(failing)}/{len(results)}")
            for pk in failing:
                print(f"   - {pk}")

        return 1 if failing else 0
    else:
        brief = get_default_brief()
        return print_pack_benchmark_issues(args.pack_key, brief)


if __name__ == "__main__":
    sys.exit(main())
