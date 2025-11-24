#!/usr/bin/env python3
"""
Phase 5 End-to-End Test: Layered Architecture with 4-Tier Pack System

Tests:
1. All 4 pack tiers are registered (Basic, Standard, Premium, Enterprise)
2. All sections for each pack have generators
3. generate_sections() works for each pack
4. Output structure is correct for each pack size
5. WOW templates are registered for each pack
6. Complete flow works: GenerateRequest → _generate_stub_output → extra_sections
"""

import sys
from datetime import date, timedelta

# Add backend to path
sys.path.insert(0, "/workspaces/AICMO")

from aicmo.presets.package_presets import PACKAGE_PRESETS
from aicmo.presets.wow_templates import WOW_TEMPLATES
from backend.main import (
    SECTION_GENERATORS,
    generate_sections,
    GenerateRequest,
    BrandBrief,
    BrandDetails,
    GoalDetails,
    AudienceDetails,
    StrategyExtras,
    _generate_stub_output,
)


def create_test_request(package_preset: str) -> GenerateRequest:
    """Create a minimal GenerateRequest for testing."""
    return GenerateRequest(
        brief=BrandBrief(
            brand=BrandDetails(
                brand_name="Test Brand",
                industry="Technology",
                product_service="Marketing Solutions",
            ),
            goal=GoalDetails(
                primary_goal="Lead Generation",
                secondary_goal="Brand Awareness",
                timeline="90 days",
            ),
            audience=AudienceDetails(
                primary_customer="Marketing Managers",
                secondary_customer="Business Owners",
            ),
            strategy_extras=StrategyExtras(
                success_30_days="Clear, measurable growth",
                brand_adjectives=["professional", "clear"],
            ),
        ),
        package_preset=package_preset,
        wow_enabled=False,
        generate_performance_review=False,
        generate_creatives=False,
    )


def test_pack_registration():
    """Test that all 4 pack tiers are registered."""
    print("\n" + "=" * 80)
    print("TEST 1: Pack Registration")
    print("=" * 80)

    required_packs = [
        "strategy_campaign_basic",
        "strategy_campaign_standard",
        "strategy_campaign_premium",
        "strategy_campaign_enterprise",
    ]

    for pack_key in required_packs:
        if pack_key in PACKAGE_PRESETS:
            pack = PACKAGE_PRESETS[pack_key]
            sections = pack.get("sections", [])
            tier = pack.get("tier", "unknown")
            print(f"✅ {pack_key}")
            print(f"   Tier: {tier}")
            print(f"   Sections: {len(sections)}")
        else:
            print(f"❌ {pack_key} NOT FOUND")
            return False

    return True


def test_generator_coverage():
    """Test that all sections have generators."""
    print("\n" + "=" * 80)
    print("TEST 2: Generator Coverage")
    print("=" * 80)

    pack_keys = [
        "strategy_campaign_basic",
        "strategy_campaign_standard",
        "strategy_campaign_premium",
        "strategy_campaign_enterprise",
    ]

    all_covered = True
    for pack_key in pack_keys:
        pack = PACKAGE_PRESETS.get(pack_key)
        if not pack:
            continue

        sections = pack.get("sections", [])
        missing = []

        for section_id in sections:
            if section_id not in SECTION_GENERATORS:
                missing.append(section_id)

        if missing:
            print(f"❌ {pack_key}: Missing generators for {missing}")
            all_covered = False
        else:
            print(f"✅ {pack_key}: 100% coverage ({len(sections)} sections)")

    return all_covered


def test_generate_sections_function():
    """Test the generate_sections() function for each pack."""
    print("\n" + "=" * 80)
    print("TEST 3: generate_sections() Function")
    print("=" * 80)

    pack_keys = [
        "strategy_campaign_basic",
        "strategy_campaign_standard",
        "strategy_campaign_premium",
        "strategy_campaign_enterprise",
    ]

    all_passed = True
    for pack_key in pack_keys:
        req = create_test_request(pack_key)
        pack = PACKAGE_PRESETS.get(pack_key)
        if not pack:
            continue

        section_ids = pack.get("sections", [])

        try:
            # Create minimal output components (would be generated in real flow)
            from backend.main import (
                MarketingPlanView,
                CampaignBlueprintView,
                SocialCalendarView,
                AudiencePersonaView,
                CampaignObjectiveView,
            )

            mp = MarketingPlanView(executive_summary="Test summary")
            cb = CampaignBlueprintView(
                big_idea="Test idea",
                objective=CampaignObjectiveView(
                    primary="test",
                    secondary="test",
                ),
                audience_persona=AudiencePersonaView(
                    name="Test",
                    description="Test",
                ),
            )
            cal = SocialCalendarView(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=6),
                posts=[],
            )

            # Test generate_sections()
            result = generate_sections(
                section_ids=section_ids,
                req=req,
                mp=mp,
                cb=cb,
                cal=cal,
            )

            # Verify results
            if len(result) != len(section_ids):
                print(f"❌ {pack_key}: Expected {len(section_ids)} sections, got {len(result)}")
                all_passed = False
            else:
                print(f"✅ {pack_key}: Generated {len(result)} sections")

        except Exception as e:
            print(f"❌ {pack_key}: Error - {str(e)}")
            all_passed = False

    return all_passed


def test_wow_templates():
    """Test that WOW templates exist for each pack."""
    print("\n" + "=" * 80)
    print("TEST 4: WOW Templates")
    print("=" * 80)

    required_templates = [
        "strategy_campaign_basic",
        "strategy_campaign_standard",
        "strategy_campaign_premium",
        "strategy_campaign_enterprise",
    ]

    all_found = True
    for template_key in required_templates:
        if template_key in WOW_TEMPLATES:
            template = WOW_TEMPLATES[template_key]
            print(f"✅ {template_key}: {len(template)} chars")
        else:
            print(f"❌ {template_key} NOT FOUND")
            all_found = False

    return all_found


def test_stub_output_generation():
    """Test _generate_stub_output() for each pack."""
    print("\n" + "=" * 80)
    print("TEST 5: Stub Output Generation")
    print("=" * 80)

    pack_keys = [
        "strategy_campaign_basic",
        "strategy_campaign_standard",
        "strategy_campaign_premium",
        "strategy_campaign_enterprise",
    ]

    all_passed = True
    for pack_key in pack_keys:
        req = create_test_request(pack_key)

        try:
            output = _generate_stub_output(req)

            pack = PACKAGE_PRESETS.get(pack_key)
            expected_sections = len(pack.get("sections", []))
            actual_sections = len(output.extra_sections)

            if actual_sections == expected_sections:
                print(f"✅ {pack_key}: {actual_sections} sections in extra_sections")
            else:
                print(f"❌ {pack_key}: Expected {expected_sections}, got {actual_sections}")
                all_passed = False

        except Exception as e:
            print(f"❌ {pack_key}: Error - {str(e)}")
            import traceback

            traceback.print_exc()
            all_passed = False

    return all_passed


def test_pack_section_counts():
    """Verify correct section counts for each pack tier."""
    print("\n" + "=" * 80)
    print("TEST 6: Pack Section Counts")
    print("=" * 80)

    expected = {
        "strategy_campaign_basic": 6,
        "strategy_campaign_standard": 17,
        "strategy_campaign_premium": 28,
        "strategy_campaign_enterprise": 39,
    }

    all_correct = True
    for pack_key, expected_count in expected.items():
        pack = PACKAGE_PRESETS.get(pack_key)
        if not pack:
            print(f"❌ {pack_key} NOT FOUND")
            all_correct = False
            continue

        actual_count = len(pack.get("sections", []))
        if actual_count == expected_count:
            print(f"✅ {pack_key}: {actual_count} sections (expected {expected_count})")
        else:
            print(f"❌ {pack_key}: {actual_count} sections (expected {expected_count})")
            all_correct = False

    return all_correct


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("PHASE 5 END-TO-END TEST: Layered Architecture")
    print("=" * 80)

    tests = [
        ("Pack Registration", test_pack_registration),
        ("Generator Coverage", test_generator_coverage),
        ("Section Counts", test_pack_section_counts),
        ("generate_sections() Function", test_generate_sections_function),
        ("WOW Templates", test_wow_templates),
        ("Stub Output Generation", test_stub_output_generation),
    ]

    results = []
    for test_name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ {test_name}: Unhandled error - {str(e)}")
            import traceback

            traceback.print_exc()
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    print("=" * 80)

    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
