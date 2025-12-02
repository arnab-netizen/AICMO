#!/usr/bin/env python3
"""
Integration test for agency PDF export path.

This simulates a real Quick Social PDF export request.
Run with: python test_agency_pdf_integration.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.export_utils import safe_export_agency_pdf

print("\n" + "=" * 80)
print("AGENCY PDF INTEGRATION TEST - Quick Social Example")
print("=" * 80 + "\n")

# Simulate a Quick Social report payload
test_report = {
    "title": "Quick Social Playbook",
    "brand_name": "Starbucks India",
    "location": "India",
    "campaign_title": "Holiday Campaign 2025",
    "campaign_duration": "30 Days",
    "brand_tone": "Friendly, inviting, premium",
    "overview_html": "<h2>Overview</h2><p>A 30-day social media strategy...</p>",
    "content_themes_html": "<h2>Content Themes</h2><ul><li>Holiday joy</li></ul>",
    "calendar_html": "<h2>Content Calendar</h2><table><tr><th>Date</th></tr></table>",
}

print("📦 Test Payload:")
print("   pack_key        = quick_social_basic")
print("   wow_enabled     = True")
print("   wow_package_key = quick_social_basic")
print(f"   report keys     = {list(test_report.keys())[:3]}...")
print()

print("🚀 Calling safe_export_agency_pdf()...")
print("-" * 80)

result = safe_export_agency_pdf(
    pack_key="quick_social_basic",
    report=test_report,
    wow_enabled=True,
    wow_package_key="quick_social_basic",
)

print("-" * 80)
print()

if result is not None:
    print(f"✅ SUCCESS: Generated {len(result)} bytes")
    print(f"   PDF header check: {result[:4] == b'%PDF'}")
    print()

    # Save to file for inspection
    output_path = Path(__file__).parent / "test_agency_pdf_output.pdf"
    output_path.write_bytes(result)
    print(f"📄 PDF saved to: {output_path}")
    print()
    print("NEXT STEPS:")
    print("1. Open test_agency_pdf_output.pdf")
    print("2. Verify no raw markdown (# ## headings)")
    print("3. Check header: 'AICMO — Marketing Intelligence Report'")
    print("4. Check page numbers at bottom")
    print("5. Verify sections are styled with boxes")

else:
    print("❌ FAILED: safe_export_agency_pdf() returned None")
    print()
    print("POSSIBLE REASONS:")
    print("- WeasyPrint not installed")
    print("- Template rendering failed")
    print("- Check debug output above for details")

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80 + "\n")
