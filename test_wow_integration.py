"""
Test/validation script for WOW template integration.

This script verifies that:
1. WOW templates can be loaded
2. Placeholders can be replaced
3. Rules can be accessed
4. The backend integration is working

Run this after integrating the WOW system:

    python test_wow_integration.py

Or from the root directory:

    python -m pytest test_wow_integration.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

# Test imports
try:
    from aicmo.presets.wow_templates import WOW_TEMPLATES
    from aicmo.presets.wow_rules import WOW_RULES
    from backend.services.wow_reports import (
        build_default_placeholders,
        apply_wow_template,
        get_wow_rules_for_package,
        resolve_wow_package_key,
    )
    from backend.export.pdf_utils import load_wow_presets, get_preset_by_key

    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    exit(1)


def test_templates_exist():
    """Verify all 7 templates exist."""
    print("\n📋 Testing templates...")
    expected_keys = {
        "quick_social_basic",
        "strategy_campaign_standard",
        "full_funnel_premium",
        "launch_gtm",
        "brand_turnaround",
        "retention_crm",
        "performance_audit",
        "fallback_basic",
    }

    actual_keys = set(WOW_TEMPLATES.keys())
    assert actual_keys == expected_keys, f"Missing templates: {expected_keys - actual_keys}"

    for key, template in WOW_TEMPLATES.items():
        assert isinstance(template, str), f"Template {key} is not a string"
        assert len(template) > 100, f"Template {key} is too short ({len(template)} chars)"
        assert "{{" in template, f"Template {key} has no placeholders"
        placeholder_count = template.count("{{")
        print(f"  ✅ {key} ({len(template)} chars, {placeholder_count} placeholders)")


def test_rules_exist():
    """Verify all 7 rule sets exist."""
    print("\n📋 Testing rules...")
    expected_keys = {
        "quick_social_basic",
        "strategy_campaign_standard",
        "full_funnel_premium",
        "launch_gtm",
        "brand_turnaround",
        "retention_crm",
        "performance_audit",
    }

    actual_keys = set(WOW_RULES.keys())
    assert actual_keys == expected_keys, f"Missing rules: {expected_keys - actual_keys}"

    for key, rules in WOW_RULES.items():
        assert isinstance(rules, dict), f"Rules {key} is not a dict"
        assert len(rules) > 0, f"Rules {key} is empty"
        print(f"  ✅ {key} ({len(rules)} rules)")


def test_presets_json():
    """Verify wow_presets.json is valid and complete."""
    print("\n📋 Testing presets JSON...")
    presets_path = Path("aicmo/presets/wow_presets.json")

    assert presets_path.exists(), f"wow_presets.json not found at {presets_path}"

    with open(presets_path) as f:
        presets = json.load(f)

    assert "version" in presets, "Missing version key"
    assert "presets" in presets, "Missing presets key"
    assert isinstance(presets["presets"], list), "presets is not a list"
    assert len(presets["presets"]) == 7, f"Expected 7 presets, got {len(presets['presets'])}"

    for preset in presets["presets"]:
        assert "key" in preset, "Preset missing key"
        assert "label" in preset, "Preset missing label"
        assert "tier" in preset, "Preset missing tier"
        assert "sections" in preset, "Preset missing sections"
        print(f"  ✅ {preset['key']} - {preset['label']} ({preset['tier']})")


def test_placeholder_replacement():
    """Verify placeholders can be replaced."""
    print("\n🔄 Testing placeholder replacement...")

    placeholders = {"brand_name": "Acme Corp", "category": "B2B SaaS"}

    result = apply_wow_template(
        package_key="quick_social_basic",
        placeholder_values=placeholders,
        strip_unfilled=False,
    )

    # Result should contain the brand name
    assert "Acme Corp" in result, "Brand name not found in result"
    print("  ✅ Placeholders replaced correctly")


def test_default_placeholders():
    """Verify build_default_placeholders works."""
    print("\n🎯 Testing default placeholders...")

    brief = {
        "brand_name": "Test Brand",
        "category": "Tech",
        "target_audience": "Developers",
    }

    blocks = {
        "calendar_14_day_table": "| Day | Content |\n|-----|---------|",
    }

    placeholders = build_default_placeholders(brief=brief, base_blocks=blocks)

    assert placeholders["brand_name"] == "Test Brand", "Brand name not in placeholders"
    assert placeholders["category"] == "Tech", "Category not in placeholders"
    assert (
        placeholders["calendar_14_day_table"] == blocks["calendar_14_day_table"]
    ), "Block not in placeholders"
    print(f"  ✅ Built {len(placeholders)} placeholders")


def test_package_key_resolution():
    """Verify package key mapping works."""
    print("\n🔗 Testing package key resolution...")

    test_cases = [
        ("Quick Social Pack (Basic)", "quick_social_basic"),
        ("Strategy + Campaign Pack (Standard)", "strategy_campaign_standard"),
        ("Full-Funnel Growth Suite (Premium)", "full_funnel_premium"),
        (None, None),
        ("Invalid Label", None),
    ]

    for label, expected_key in test_cases:
        result = resolve_wow_package_key(label)
        assert result == expected_key, f"Expected {expected_key}, got {result} for {label}"
        print(f"  ✅ {label or '(None)'} → {result or '(None)'}")


def test_rules_access():
    """Verify rules can be accessed safely."""
    print("\n📊 Testing rules access...")

    # Valid key
    rules = get_wow_rules_for_package("quick_social_basic")
    assert isinstance(rules, dict), "Rules should be a dict"
    assert len(rules) > 0, "Rules should not be empty"
    print(f"  ✅ quick_social_basic has {len(rules)} rules")

    # Invalid key
    rules = get_wow_rules_for_package("nonexistent")
    assert rules == {}, "Invalid key should return empty dict"
    print("  ✅ Invalid key returns empty dict (safe fallback)")


def test_preset_loading():
    """Verify presets can be loaded from disk."""
    print("\n💾 Testing preset loading...")

    presets = load_wow_presets()
    assert isinstance(presets, dict), "Presets should be a dict"
    assert "presets" in presets, "Should have presets key"
    assert len(presets["presets"]) == 7, "Should have 7 presets"
    print(f"  ✅ Loaded {len(presets['presets'])} presets from disk")

    # Test get_preset_by_key
    preset = get_preset_by_key("quick_social_basic")
    assert preset is not None, "Should find preset by key"
    assert preset["key"] == "quick_social_basic", "Preset key mismatch"
    print(f"  ✅ Retrieved preset by key: {preset['label']}")

    # Invalid key
    preset = get_preset_by_key("nonexistent")
    assert preset is None, "Invalid key should return None"
    print("  ✅ Invalid key returns None (safe fallback)")


def test_template_stripping():
    """Verify unfilled placeholders are stripped."""
    print("\n🧹 Testing placeholder stripping...")

    result = apply_wow_template(
        package_key="quick_social_basic",
        placeholder_values={"brand_name": "Test"},  # Only provide one value
        strip_unfilled=True,
    )

    # Should not contain any {{ }} patterns
    assert "{{" not in result, "Unfilled placeholders not stripped"
    assert "}}" not in result, "Unfilled placeholders not stripped"
    assert "Test" in result, "Provided placeholder not in result"
    print("  ✅ Unfilled placeholders stripped, result is clean")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("🧪 WOW TEMPLATE INTEGRATION TEST SUITE")
    print("=" * 60)

    tests = [
        test_templates_exist,
        test_rules_exist,
        test_presets_json,
        test_default_placeholders,
        test_package_key_resolution,
        test_rules_access,
        test_preset_loading,
        test_placeholder_replacement,
        test_template_stripping,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {test_func.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ {test_func.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
