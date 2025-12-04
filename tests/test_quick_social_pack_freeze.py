"""
Quick Social Pack (Basic) - Freeze & Protection Tests

Purpose: Verify protection safeguards are in place for Quick Social Pack.
This test ensures that:
  - Protection headers are present in all generator functions
  - WOW template has defensive comments
  - Documentation is accessible
  
Run this test to verify protection infrastructure is intact before making changes.

Usage:
    pytest tests/test_quick_social_pack_freeze.py -v
    python tests/test_quick_social_pack_freeze.py
"""

import os
import sys
import re

# Add project root to path
sys.path.insert(0, "/workspaces/AICMO")


class TestQuickSocialPackProtection:
    """Protection tests to ensure safeguards are in place."""

    GENERATOR_FUNCTIONS = [
        "_gen_overview",
        "_gen_messaging_framework",
        "_gen_quick_social_30_day_calendar",
        "_gen_content_buckets",
        "_gen_hashtag_strategy",
        "_gen_kpi_plan_light",
        "_gen_execution_roadmap",
        "_gen_final_summary",
    ]

    PROTECTION_MARKER = "PRODUCTION-VERIFIED"
    TEST_COMMANDS = [
        "python test_hashtag_validation.py",
        "python test_full_pack_real_generators.py",
        "python scripts/dev_validate_benchmark_proof.py",
        "python tests/test_quick_social_pack_freeze.py",
    ]

    def test_generator_protection_headers_exist(self):
        """Verify all Quick Social generators have protection headers."""
        backend_main_path = "/workspaces/AICMO/backend/main.py"

        with open(backend_main_path, "r", encoding="utf-8") as f:
            content = f.read()

        for func_name in self.GENERATOR_FUNCTIONS:
            # Find function definition (capture everything from def to end of docstring)
            func_start = content.find(f"def {func_name}(")

            assert func_start != -1, f"Function {func_name} not found in backend/main.py"

            # Extract docstring (next 1000 chars should contain it)
            func_section = content[func_start : func_start + 1000]

            assert (
                self.PROTECTION_MARKER in func_section
            ), f"Function {func_name} missing protection header marker '{self.PROTECTION_MARKER}'"

            # Check that at least one test command is mentioned
            has_test_ref = any(cmd in func_section for cmd in self.TEST_COMMANDS)
            assert has_test_ref, f"Function {func_name} missing test command references"

    def test_wow_template_has_protection_comments(self):
        """Verify WOW template has defensive comments."""
        wow_template_path = "/workspaces/AICMO/aicmo/presets/wow_templates.py"

        with open(wow_template_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find quick_social_basic template
        pattern = r'"quick_social_basic":\s*r"""(.*?)"""'
        match = re.search(pattern, content, re.DOTALL)

        assert match is not None, "quick_social_basic template not found"

        template_content = match.group(1)

        # Check for protection comments
        assert (
            self.PROTECTION_MARKER in template_content
        ), "WOW template missing production-verified marker"

        assert "DO NOT change" in template_content, "WOW template missing 'DO NOT change' warning"

    def test_documentation_files_exist(self):
        """Verify protection documentation exists."""
        required_docs = [
            "/workspaces/AICMO/QUICK_SOCIAL_PACK_FINAL_CLIENT_READY.md",
            "/workspaces/AICMO/QUICK_SOCIAL_FINAL_STATUS.md",
            "/workspaces/AICMO/QUICK_SOCIAL_PACK_DOCUMENTATION_INDEX.md",
        ]

        for doc_path in required_docs:
            assert os.path.exists(doc_path), f"Required documentation missing: {doc_path}"

    def test_snapshot_utility_exists(self):
        """Verify snapshot utility is available."""
        snapshot_path = "/workspaces/AICMO/backend/utils/non_regression_snapshot.py"
        assert os.path.exists(snapshot_path), f"Snapshot utility missing: {snapshot_path}"

        # Check it has key functions
        with open(snapshot_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "create_snapshot" in content, "Snapshot utility missing create_snapshot function"
        assert "compare_snapshots" in content, "Snapshot utility missing compare_snapshots function"


def run_protection_test():
    """Run all protection tests and print results."""
    print("=" * 70)
    print("QUICK SOCIAL PACK (BASIC) - PROTECTION TEST")
    print("=" * 70)
    print()

    test_instance = TestQuickSocialPackProtection()
    tests = [
        ("Generator protection headers", test_instance.test_generator_protection_headers_exist),
        ("WOW template protection", test_instance.test_wow_template_has_protection_comments),
        ("Documentation files", test_instance.test_documentation_files_exist),
        ("Snapshot utility", test_instance.test_snapshot_utility_exists),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✅ PASS: {test_name}")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {test_name}")
            print(f"   Error: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"⚠️  ERROR: {test_name}")
            print(f"   Exception: {str(e)}")
            failed += 1

    print()
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("🎉 ALL PROTECTION TESTS PASSED - Safeguards are in place!")
        return 0
    else:
        print("⚠️  PROTECTION TESTS FAILED - Safeguards missing!")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(run_protection_test())
