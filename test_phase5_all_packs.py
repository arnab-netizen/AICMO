#!/usr/bin/env python3
"""
Phase 5 End-to-End Test: Verify all 4 pack tiers work correctly
- Validates section registry completeness
- Validates WOW templates have placeholders for all sections
- Tests generator function availability for all sections
"""

import sys

# Add parent directory to path
sys.path.insert(0, "/workspaces/AICMO")

from aicmo.presets.package_presets import PACKAGE_PRESETS
from aicmo.presets.wow_templates import WOW_TEMPLATES
from backend.main import SECTION_GENERATORS


def test_pack_tier(pack_slug: str) -> dict:
    """Test a single pack tier and return results."""
    print(f"\n{'='*70}")
    print(f"Testing: {pack_slug}")
    print("=" * 70)

    # Get pack preset
    if pack_slug not in PACKAGE_PRESETS:
        return {
            "slug": pack_slug,
            "status": "FAIL",
            "error": "Pack not found in PACKAGE_PRESETS",
        }

    preset = PACKAGE_PRESETS[pack_slug]
    expected_sections = preset.get("sections", [])
    expected_count = len(expected_sections)

    print(f"✓ Pack found: {preset.get('label')}")
    print(f"✓ Tier: {preset.get('tier', 'unknown')}")
    print(f"✓ Expected sections: {expected_count}")
    print(
        f"  Sections: {', '.join(expected_sections[:5])}{'...' if len(expected_sections) > 5 else ''}"
    )

    # Check WOW template exists
    if pack_slug not in WOW_TEMPLATES:
        return {
            "slug": pack_slug,
            "status": "FAIL",
            "error": f"WOW template not found for {pack_slug}",
            "expected_count": expected_count,
            "actual_count": 0,
        }

    template = WOW_TEMPLATES[pack_slug]
    print(f"✓ WOW template found ({len(template)} chars)")

    # Check all sections have generators
    missing_generators = []
    for section_id in expected_sections:
        if section_id not in SECTION_GENERATORS:
            missing_generators.append(section_id)

    if missing_generators:
        print(f"✓ Missing generators: {len(missing_generators)} sections")
        for sid in missing_generators[:5]:
            print(f"  - {sid}")

    # Verify template has all placeholders
    template_errors = []
    for section_id in expected_sections:
        placeholder = f"{{{{{section_id}}}}}"
        if placeholder not in template:
            template_errors.append(section_id)

    if template_errors:
        print(f"⚠ Template missing placeholders for: {len(template_errors)} sections")
        for sid in template_errors[:5]:
            print(f"  - {sid}")

    status = "SUCCESS"
    if missing_generators:
        status = "PARTIAL"
    if template_errors:
        status = "PARTIAL"

    return {
        "slug": pack_slug,
        "status": status,
        "expected_count": expected_count,
        "template_size": len(template),
        "missing_generators": len(missing_generators),
        "template_errors": len(template_errors),
    }


def main():
    print("\n" + "=" * 70)
    print("PHASE 5 END-TO-END TEST: All 4 Pack Tiers")
    print("=" * 70)

    # Define the 4 pack tiers to test
    pack_tiers = [
        ("strategy_campaign_basic", "BASIC - 6 sections, simple"),
        ("strategy_campaign_standard", "STANDARD - 17 sections, professional"),
        ("strategy_campaign_premium", "PREMIUM - 28 sections, comprehensive"),
        ("strategy_campaign_enterprise", "ENTERPRISE - 39 sections, consulting-grade"),
    ]

    results = []
    for pack_slug, description in pack_tiers:
        print(f"\n{description}")
        result = test_pack_tier(pack_slug)
        results.append(result)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    all_success = True
    for result in results:
        status_icon = (
            "✅"
            if result["status"] == "SUCCESS"
            else ("⚠" if result["status"] == "PARTIAL" else "❌")
        )
        print(f"{status_icon} {result['slug']}: {result['status']}")

        if "expected_count" in result:
            print(f"   Template: {result['template_size']} chars")
            if result.get("missing_generators"):
                print(f"   Missing generators: {result['missing_generators']}")
            if result.get("template_errors"):
                print(f"   Missing placeholders: {result['template_errors']}")

        if "error" in result:
            print(f"   Error: {result['error']}")

        if result["status"] != "SUCCESS":
            all_success = False

    print("\n" + "=" * 70)
    print(f"Generator Coverage: {len(SECTION_GENERATORS)} sections registered")
    print("=" * 70)

    print("\n" + "=" * 70)
    print(f"Overall: {'✅ ALL TESTS PASSED' if all_success else '⚠ SOME TESTS NEED ATTENTION'}")
    print("=" * 70)

    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
