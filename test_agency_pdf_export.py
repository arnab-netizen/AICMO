#!/usr/bin/env python3
"""
Test script to verify agency PDF path selection.

This demonstrates which path (AGENCY vs MARKDOWN) is chosen based on payload.

Run with: python test_agency_pdf_export.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.export_utils import should_use_agency_pdf

print("\n" + "=" * 80)
print("AGENCY PDF PATH SELECTION TEST")
print("=" * 80 + "\n")

# Test Case 1: Quick Social with WOW enabled (SHOULD use agency)
print("TEST 1: Quick Social with WOW enabled")
print("-" * 40)
result = should_use_agency_pdf(
    pack_key="quick_social_basic", wow_enabled=True, wow_package_key="quick_social_basic"
)
print(f"✅ should_use_agency_pdf() = {result}")
print("Expected: True\n")

# Test Case 2: Quick Social WITHOUT WOW (SHOULD NOT use agency)
print("TEST 2: Quick Social WITHOUT WOW enabled")
print("-" * 40)
result = should_use_agency_pdf(
    pack_key="quick_social_basic", wow_enabled=False, wow_package_key="quick_social_basic"
)
print(f"✅ should_use_agency_pdf() = {result}")
print("Expected: False\n")

# Test Case 3: Campaign Strategy with WOW (SHOULD use agency)
print("TEST 3: Campaign Strategy with WOW enabled")
print("-" * 40)
result = should_use_agency_pdf(
    pack_key="strategy_campaign_standard",
    wow_enabled=True,
    wow_package_key="strategy_campaign_standard",
)
print(f"✅ should_use_agency_pdf() = {result}")
print("Expected: True\n")

# Test Case 4: Unknown pack (SHOULD NOT use agency)
print("TEST 4: Unknown pack")
print("-" * 40)
result = should_use_agency_pdf(
    pack_key="unknown_pack", wow_enabled=True, wow_package_key="unknown_pack"
)
print(f"✅ should_use_agency_pdf() = {result}")
print("Expected: False\n")

# Test Case 5: No wow_package_key (SHOULD NOT use agency)
print("TEST 5: No wow_package_key")
print("-" * 40)
result = should_use_agency_pdf(
    pack_key="quick_social_basic", wow_enabled=True, wow_package_key=None
)
print(f"✅ should_use_agency_pdf() = {result}")
print("Expected: False\n")

print("\n" + "=" * 80)
print("TEST COMPLETE - Check console output above")
print("=" * 80 + "\n")

print("NEXT STEPS:")
print("-" * 40)
print("1. Export a Quick Social PDF from the UI with WOW enabled")
print("2. Check the console for debug output showing:")
print("   - should_use_agency_pdf() conditions")
print("   - Which path was chosen (AGENCY or MARKDOWN)")
print("   - Template name used (quick_social_basic.html)")
print("3. Open the PDF and verify:")
print("   - No literal markdown (# ## headings)")
print("   - Header: 'AICMO — Marketing Intelligence Report'")
print("   - Page numbers at bottom")
print("   - Styled sections and tables")
print("\n")
