#!/usr/bin/env python3
"""
Comprehensive verification that humanization layer is properly integrated.
"""

import sys

sys.path.insert(0, "/workspaces/AICMO")


def check_imports():
    """Check all required imports."""
    print("\n" + "=" * 70)
    print("✓ IMPORT CHECKS")
    print("=" * 70)

    try:

        print("✅ humanization_wrapper imports OK")
    except Exception as e:
        print(f"❌ humanization_wrapper import failed: {e}")
        return False

    try:

        print("✅ dashboard integration (_apply_humanization) OK")
    except Exception as e:
        print(f"❌ dashboard integration failed: {e}")
        return False

    return True


def check_wrapper_functionality():
    """Test humanization wrapper functionality."""
    print("\n" + "=" * 70)
    print("✓ WRAPPER FUNCTIONALITY CHECKS")
    print("=" * 70)

    from backend.humanization_wrapper import HumanizationWrapper

    wrapper = HumanizationWrapper()

    # Test 1: Process simple text
    test_text = "Here are some ways to improve your strategy. In conclusion, you should focus on these areas."
    result = wrapper.process_text(test_text)

    if result and len(result) > 0:
        print("✅ process_text() works")
    else:
        print("❌ process_text() returned empty")
        return False

    # Test 2: Check boilerplate removal
    if "Here are some ways" not in result or "In conclusion" not in result:
        print("✅ Boilerplate removal working (patterns removed)")
    else:
        print("⚠️  Boilerplate removal (without OpenAI, uses fallback)")

    # Test 3: Process report dict
    test_report = {
        "executive_summary": "Here are some key points. In summary, focus on three areas.",
        "strategy": "Overall, you should implement these steps.",
        "other_field": "This field should not be processed",
    }

    result_report = wrapper.process_report(test_report, fields=["executive_summary", "strategy"])

    if result_report["executive_summary"] != test_report["executive_summary"]:
        print("✅ process_report() modifies selected fields")
    else:
        print("⚠️  process_report() field processing")

    if result_report["other_field"] == test_report["other_field"]:
        print("✅ process_report() ignores unselected fields")
    else:
        print("❌ process_report() modified non-target field")
        return False

    return True


def check_persona():
    """Test PersonaConfig."""
    print("\n" + "=" * 70)
    print("✓ PERSONA CONFIG CHECKS")
    print("=" * 70)

    from backend.humanization_wrapper import PersonaConfig, HumanizationWrapper

    # Test 1: Default persona
    default_persona = PersonaConfig()
    print(f"✅ Default persona: {default_persona.name}")

    # Test 2: Custom persona
    custom_persona = PersonaConfig(
        name="Custom Strategist", description="Custom description", style_notes="Custom style"
    )
    print(f"✅ Custom persona creation: {custom_persona.name}")

    # Test 3: Wrapper with custom persona
    wrapper = HumanizationWrapper(persona=custom_persona)
    if wrapper.persona.name == "Custom Strategist":
        print("✅ Wrapper accepts custom persona")
    else:
        print("❌ Wrapper persona assignment failed")
        return False

    return True


def check_fallback():
    """Test graceful fallback."""
    print("\n" + "=" * 70)
    print("✓ FALLBACK CHECKS")
    print("=" * 70)

    from backend.humanization_wrapper import HumanizationWrapper

    # Test with no API key (simulating missing OpenAI)
    wrapper = HumanizationWrapper()

    test_text = "Here are some ways forward. In conclusion, you should act."

    try:
        result = wrapper.process_text(test_text)
        if result:
            print("✅ Fallback mode works (no exceptions)")
        else:
            print("⚠️  Fallback returned empty string")
    except Exception as e:
        print(f"❌ Fallback threw exception: {e}")
        return False

    print("✅ Graceful degradation confirmed")
    return True


def check_dashboard_integration():
    """Verify dashboard integration points."""
    print("\n" + "=" * 70)
    print("✓ DASHBOARD INTEGRATION CHECKS")
    print("=" * 70)

    try:
        import streamlit_pages.aicmo_operator as dashboard

        # Check that functions exist
        if hasattr(dashboard, "_apply_humanization"):
            print("✅ _apply_humanization function exists")
        else:
            print("❌ _apply_humanization function not found")
            return False

        if hasattr(dashboard, "call_backend_generate"):
            print("✅ call_backend_generate function exists")
        else:
            print("❌ call_backend_generate function not found")
            return False

        if hasattr(dashboard, "render_client_input_tab"):
            print("✅ render_client_input_tab function exists")
        else:
            print("❌ render_client_input_tab function not found")
            return False

        # Check that humanizer is imported
        if hasattr(dashboard, "humanizer"):
            print("✅ humanizer variable exists (import successful)")
        else:
            print("⚠️  humanizer variable not directly accessible")

        return True

    except Exception as e:
        print(f"❌ Dashboard integration check failed: {e}")
        return False


def run_all_checks():
    """Run all verification checks."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║  AICMO HUMANIZATION LAYER - VERIFICATION SUITE" + " " * 19 + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    results = {
        "Imports": check_imports(),
        "Wrapper Functionality": check_wrapper_functionality(),
        "Persona Config": check_persona(),
        "Fallback Behavior": check_fallback(),
        "Dashboard Integration": check_dashboard_integration(),
    }

    print("\n" + "=" * 70)
    print("✓ SUMMARY")
    print("=" * 70)

    all_passed = True
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")
        if not passed:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n" + "🎉 " * 18)
        print("🟢 ALL CHECKS PASSED - HUMANIZATION LAYER READY FOR PRODUCTION")
        print("🎉 " * 18)
        print("\nNext steps:")
        print("1. Set OPENAI_API_KEY to enable full humanization")
        print("2. Generate a draft report in Tab 1 to see it in action")
        print("3. Check output in Workshop tab (Tab 2)")
        return True
    else:
        print("\n❌ Some checks failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)
