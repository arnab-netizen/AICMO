"""
Direct tests for Phase L framework injection without conftest dependency.

Tests run the processing functions directly without pytest fixtures
to avoid the async/greenlet conftest issue.
"""

import os
import sys

# Add workspace root to path
sys.path.insert(0, "/workspaces/AICMO")

# Set test environment before imports
os.environ["AICMO_USE_LLM"] = "0"
os.environ["AICMO_TURBO_ENABLED"] = "0"


def test_framework_injection_direct():
    """Direct test: framework injection without pytest fixtures."""
    from aicmo.generators.agency_grade_processor import _inject_frameworks_into_report
    from aicmo.memory.engine import count_items, retrieve_relevant_context
    from aicmo.presets.framework_fusion import structure_learning_context

    # Verify memory is available
    count = count_items()
    print(f"✅ Memory has {count} items")
    assert count > 0, "Memory engine should be populated"

    # Get learning context
    context_raw = retrieve_relevant_context("marketing technology strategy")
    print(f"✅ Retrieved {len(context_raw)} chars of learning context")

    # Structure the learning context
    struct = structure_learning_context(context_raw) if context_raw else {}
    print(f"✅ Structured learning context into {len(struct)} keys")

    # Test the injection function directly
    class MockReport:
        class MockMarketingPlan:
            strategy = "Original strategy text"

        marketing_plan = MockMarketingPlan()
        campaign_blueprint = {"briefing": "Original briefing"}
        extra_sections = {}

    report = MockReport()
    frameworks_str = struct.get("core_frameworks", "")

    if frameworks_str:
        _inject_frameworks_into_report(report, "Test brand", struct)
        print("✅ Framework injection executed (frameworks available)")
    else:
        print("✅ Framework injection skipped gracefully (no frameworks)")

    return True


def test_language_filters_direct():
    """Direct test: language filters without pytest fixtures."""
    from aicmo.generators.language_filters import apply_all_filters
    from aicmo.generators.agency_grade_processor import _apply_language_filters_to_report

    # Test the filter function
    test_text = "This is a very great amazing unique opportunity for growth"
    filtered = apply_all_filters(test_text)

    assert isinstance(filtered, str)
    print(f"✅ Language filter applied: '{test_text}' -> '{filtered}'")

    # Test the filter application function with mock report
    class MockReport:
        class MockMarketingPlan:
            executive_summary = test_text
            strategy = test_text

        marketing_plan = MockMarketingPlan()
        campaign_blueprint = {"briefing": test_text}
        extra_sections = {"Creative Direction": test_text}

    report = MockReport()
    _apply_language_filters_to_report(report)
    print("✅ Language filters applied to report sections")

    return True


def test_memory_integration_direct():
    """Direct test: memory engine integration."""
    from aicmo.memory.engine import (
        retrieve_relevant_context,
        count_items,
        get_db_url,
    )

    # Test retrieval
    db_url = get_db_url()
    print(f"✅ Database URL: {db_url}")

    count = count_items()
    print(f"✅ Memory items: {count}")
    assert count > 0

    # Test context retrieval
    context = retrieve_relevant_context("test marketing strategy")
    assert isinstance(context, str)
    print(f"✅ Retrieved {len(context)} chars of context")

    return True


def test_backend_integration_direct():
    """Direct test: backend integration."""
    from backend.main import _retrieve_learning_context

    # Test the backend helper
    raw, struct = _retrieve_learning_context("Test marketing brief")

    assert isinstance(raw, str)
    assert isinstance(struct, dict)
    print(f"✅ Backend retrieved {len(raw)} chars raw, {len(struct)} struct keys")

    if struct:
        expected_keys = {
            "core_frameworks",
            "thinking_sequences",
            "reasoning_patterns",
            "structure_rules",
            "premium_expressions",
            "creative_hooks",
        }
        assert set(struct.keys()) == expected_keys
        print("✅ Structured learning context has all expected keys")

    return True


if __name__ == "__main__":
    tests = [
        ("Memory Integration", test_memory_integration_direct),
        ("Backend Integration", test_backend_integration_direct),
        ("Framework Injection", test_framework_injection_direct),
        ("Language Filters", test_language_filters_direct),
    ]

    print("\n" + "=" * 70)
    print("RUNNING DIRECT INTEGRATION TESTS (no conftest)")
    print("=" * 70 + "\n")

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n[TEST] {test_name}...")
            test_func()
            print(f"✅ PASSED: {test_name}\n")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {test_name}")
            print(f"   Error: {e}\n")
            failed += 1
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")

    sys.exit(0 if failed == 0 else 1)
