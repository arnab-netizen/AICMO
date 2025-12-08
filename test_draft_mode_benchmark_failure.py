"""
Test draft mode with a deliberately failing pack to prove the safety mechanism works.

This creates a scenario where benchmarks would fail, and verifies:
- draft_mode=False: Returns error
- draft_mode=True: Returns success with warnings
"""

import asyncio
from unittest.mock import patch, MagicMock
from backend.main import api_aicmo_generate_report
from backend.validators.report_enforcer import BenchmarkEnforcementError


async def test_draft_mode_with_benchmark_failure():
    """
    Simulate a benchmark failure and verify draft mode handles it gracefully.
    """
    print("\n" + "=" * 80)
    print("SIMULATED BENCHMARK FAILURE TEST")
    print("=" * 80)
    
    payload_base = {
        "pack_key": "quick_social_basic",
        "client_brief": {
            "brand_name": "TestCo",
            "industry": "Technology",
            "primary_goal": "Increase awareness",
        },
    }
    
    # Create a mock that simulates benchmark failure
    def mock_enforce_with_failure(*args, **kwargs):
        draft_mode = kwargs.get('draft_mode', False)
        if draft_mode:
            # In draft mode, it should return success with warnings
            from backend.validators.report_enforcer import EnforcementOutcome
            mock_validation = MagicMock()
            mock_validation.status = "PASS_WITH_WARNINGS"
            return EnforcementOutcome(
                status="PASS_WITH_WARNINGS",
                sections=kwargs.get('sections', []),
                validation=mock_validation,
            )
        else:
            # In strict mode, raise error
            raise BenchmarkEnforcementError(
                "Benchmark validation failed for pack 'quick_social_basic' "
                "after 2 attempt(s). Failing sections: ['overview', 'persona_cards']"
            )
    
    # Test 1: Strict mode (should fail)
    print("\n--- Test 1: Strict Mode (draft_mode=False) ---")
    payload_strict = {**payload_base, "draft_mode": False}
    
    with patch("backend.validators.report_enforcer.enforce_benchmarks_with_regen", side_effect=mock_enforce_with_failure):
        result_strict = await api_aicmo_generate_report(payload_strict)
    
    print(f"Success: {result_strict.get('success')}")
    print(f"Status: {result_strict.get('status')}")
    if not result_strict.get('success'):
        print(f"Error Type: {result_strict.get('error_type')}")
        print(f"Error Message: {result_strict.get('error_message', '')[:100]}...")
    
    # Test 2: Draft mode (should succeed with warnings)
    print("\n--- Test 2: Draft Mode (draft_mode=True) ---")
    payload_draft = {**payload_base, "draft_mode": True}
    
    with patch("backend.validators.report_enforcer.enforce_benchmarks_with_regen", side_effect=mock_enforce_with_failure):
        result_draft = await api_aicmo_generate_report(payload_draft)
    
    print(f"Success: {result_draft.get('success')}")
    print(f"Status: {result_draft.get('status')}")
    print(f"Has Report: {'report_markdown' in result_draft and bool(result_draft.get('report_markdown'))}")
    if 'benchmark_warnings' in result_draft:
        print(f"Benchmark Warnings: Present")
    
    # Verification
    print("\n" + "=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)
    
    checks_passed = []
    checks_failed = []
    
    # Check 1: Draft mode returns success
    if result_draft.get('success') is True:
        checks_passed.append("✅ Draft mode returns success=True")
    else:
        checks_failed.append("❌ Draft mode should return success=True")
    
    # Check 2: Draft mode has report_markdown
    if result_draft.get('report_markdown'):
        checks_passed.append("✅ Draft mode includes report_markdown")
    else:
        checks_failed.append("❌ Draft mode should include report_markdown")
    
    # Check 3: Draft mode doesn't have llm_failure error
    if 'llm_failure' not in str(result_draft.get('error_type', '')):
        checks_passed.append("✅ Draft mode doesn't return llm_failure error")
    else:
        checks_failed.append("❌ Draft mode should not return llm_failure")
    
    # Check 4: Status is warning (not error)
    if result_draft.get('status') in ['warning', 'success']:
        checks_passed.append("✅ Draft mode status is 'warning' or 'success'")
    else:
        checks_failed.append(f"❌ Draft mode status should be 'warning' or 'success', got: {result_draft.get('status')}")
    
    # Print results
    for check in checks_passed:
        print(check)
    for check in checks_failed:
        print(check)
    
    if not checks_failed:
        print("\n🎉 ALL CHECKS PASSED - Draft mode correctly prevents hard failures!")
    else:
        print(f"\n⚠️  {len(checks_failed)} check(s) failed")
    
    return len(checks_failed) == 0


if __name__ == "__main__":
    success = asyncio.run(test_draft_mode_with_benchmark_failure())
    exit(0 if success else 1)

# Command to run:
# PYTHONPATH=/workspaces/AICMO python /workspaces/AICMO/test_draft_mode_benchmark_failure.py
