"""
Demonstrate that draft_mode works correctly for full_funnel_growth_suite.

This script tests both modes:
1. draft_mode=False (strict) - may fail if benchmarks don't pass
2. draft_mode=True (draft) - should succeed with warnings even if benchmarks fail

Results are printed to show the difference in behavior.
"""

import asyncio
import json
from backend.client.aicmo_api_client import call_generate_report


def test_full_funnel_strict_mode():
    """Test full_funnel_growth_suite in strict mode."""
    print("\n" + "=" * 80)
    print("TEST 1: full_funnel_growth_suite with draft_mode=False (STRICT)")
    print("=" * 80)
    
    payload = {
        "pack_key": "full_funnel_growth_suite",
        "client_brief": {
            "brand_name": "TechFlow Solutions",
            "industry": "Technology",
            "product_service": "Cloud-based project management software",
            "primary_goal": "Generate qualified leads and increase trial signups by 40%",
            "target_audience": "Project managers and team leads at mid-sized tech companies",
            "geography": "North America",
            "budget": "$50,000/month",
            "timeline": "Q1 2025",
            "constraints": "Must comply with GDPR and SOC2 requirements",
        },
        "draft_mode": False,  # STRICT MODE
    }
    
    result = call_generate_report(payload)
    
    print(f"\n✓ Success: {result.get('success')}")
    print(f"✓ Status: {result.get('status')}")
    print(f"✓ Pack Key: {result.get('pack_key')}")
    
    if result.get('success'):
        print(f"✓ Report Length: {len(result.get('report_markdown', ''))} chars")
        print(f"✓ Stub Used: {result.get('stub_used')}")
        print(f"✓ Quality Passed: {result.get('quality_passed')}")
    else:
        print(f"✗ Error Type: {result.get('error_type')}")
        print(f"✗ Error Message: {result.get('error_message', '')[:200]}")
    
    return result


def test_full_funnel_draft_mode():
    """Test full_funnel_growth_suite in draft mode."""
    print("\n" + "=" * 80)
    print("TEST 2: full_funnel_growth_suite with draft_mode=True (DRAFT)")
    print("=" * 80)
    
    payload = {
        "pack_key": "full_funnel_growth_suite",
        "client_brief": {
            "brand_name": "TechFlow Solutions",
            "industry": "Technology",
            "product_service": "Cloud-based project management software",
            "primary_goal": "Generate qualified leads and increase trial signups by 40%",
            "target_audience": "Project managers and team leads at mid-sized tech companies",
            "geography": "North America",
            "budget": "$50,000/month",
            "timeline": "Q1 2025",
            "constraints": "Must comply with GDPR and SOC2 requirements",
        },
        "draft_mode": True,  # DRAFT MODE
    }
    
    result = call_generate_report(payload)
    
    print(f"\n✓ Success: {result.get('success')}")
    print(f"✓ Status: {result.get('status')}")
    print(f"✓ Pack Key: {result.get('pack_key')}")
    
    if result.get('success'):
        print(f"✓ Report Length: {len(result.get('report_markdown', ''))} chars")
        print(f"✓ Stub Used: {result.get('stub_used')}")
        print(f"✓ Quality Passed: {result.get('quality_passed')}")
        
        # Check for benchmark warnings
        if 'benchmark_warnings' in result:
            print(f"\n⚠️  Benchmark Warnings Present:")
            warnings = result['benchmark_warnings']
            if isinstance(warnings, str):
                print(f"   {warnings[:200]}...")
            else:
                print(f"   {json.dumps(warnings, indent=2)[:300]}...")
    else:
        print(f"✗ Error Type: {result.get('error_type')}")
        print(f"✗ Error Message: {result.get('error_message', '')[:200]}")
        print("\n❌ DRAFT MODE SHOULD NOT FAIL - This is unexpected!")
    
    return result


def compare_results(strict_result, draft_result):
    """Compare strict vs draft mode results."""
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    
    print(f"\nStrict Mode:")
    print(f"  - Success: {strict_result.get('success')}")
    print(f"  - Has Report: {'report_markdown' in strict_result and bool(strict_result.get('report_markdown'))}")
    
    print(f"\nDraft Mode:")
    print(f"  - Success: {draft_result.get('success')}")
    print(f"  - Has Report: {'report_markdown' in draft_result and bool(draft_result.get('report_markdown'))}")
    print(f"  - Has Warnings: {'benchmark_warnings' in draft_result}")
    
    # Verify key requirement: draft mode should always succeed
    if draft_result.get('success') is True:
        print("\n✅ PASS: Draft mode returned success=True")
    else:
        print("\n❌ FAIL: Draft mode should always return success=True")
    
    # Verify report is present in draft mode
    if draft_result.get('report_markdown'):
        print("✅ PASS: Draft mode includes report_markdown")
    else:
        print("❌ FAIL: Draft mode should include report_markdown")
    
    # Verify no llm_failure error type
    if 'llm_failure' not in str(draft_result.get('error_type', '')):
        print("✅ PASS: No 'llm_failure' error in draft mode")
    else:
        print("❌ FAIL: Draft mode should not return llm_failure error")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DRAFT MODE VALIDATION TEST - full_funnel_growth_suite")
    print("=" * 80)
    print("\nThis test demonstrates that draft_mode=True prevents hard failures")
    print("even when benchmark validation would normally fail in strict mode.")
    
    # Run both tests
    strict_result = test_full_funnel_strict_mode()
    draft_result = test_full_funnel_draft_mode()
    
    # Compare results
    compare_results(strict_result, draft_result)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

# Command to run:
# PYTHONPATH=/workspaces/AICMO python /workspaces/AICMO/test_full_funnel_draft_mode.py
