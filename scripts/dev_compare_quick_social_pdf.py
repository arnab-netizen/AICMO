#!/usr/bin/env python3
"""
Quick Social PDF Comparison Script - Post Fix-1 Verification

This script:
1. Generates a Quick Social report with realistic brief
2. Parses markdown into sections structure
3. Captures the actual PDF context passed to templates
4. Generates PDF and extracts text content
5. Provides detailed comparison for audit

Usage:
    python scripts/dev_compare_quick_social_pdf.py
"""

import sys
import os
import re
from pathlib import Path

# Add backend to path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_path)

print("=" * 80)
print("🔍 QUICK SOCIAL PDF COMPARISON - POST FIX-1 VERIFICATION")
print("=" * 80)

# ============================================================================
# STEP 1: Generate Report with Realistic Brief
# ============================================================================

print("\n📋 STEP 1: Generating Quick Social Report")
print("-" * 80)

# Realistic brief for DemoCafe
client_brief = {
    "brand_name": "DemoCafe",
    "brand_voice": "Friendly, energetic, community-focused",
    "industry": "Coffeehouse / Beverage Retail",
    "goal": "Boost in-store footfall by 25% and increase Instagram engagement from 2% to 5%",
    "audience": "Young professionals (25-40) and college students who value artisanal coffee and cozy spaces",
    "budget_range": "Under $5k/month for boosted posts and influencer partnerships",
    "competitors": "Local cafes, Starbucks, indie coffee brands",
    "channels": "Instagram (primary), TikTok (experimental)",
    "unique_value": "Locally roasted beans, barista workshops, free Wi-Fi and study space",
    "content_preferences": "Behind-the-scenes content, customer stories, latte art showcases",
}

print(f"✓ Brief created for: {client_brief['brand_name']}")
print(f"  Industry: {client_brief['industry']}")
print(f"  Primary Channel: {client_brief['channels'].split('(')[0].strip()}")

# Generate report using public API
# Direct import from main module

print("\n⏳ Generating report (this may take a moment)...")

# Need to handle async function
# 🔥 UPDATED: Generate report and directly extract sections from stub functions
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aicmo.io.client_reports import (
    ClientInputBrief,
    BrandBrief,
    AudienceBrief,
    GoalBrief,
    VoiceBrief,
    ProductServiceBrief,
    AssetsConstraintsBrief,
    OperationsBrief,
    StrategyExtrasBrief,
)
from backend.utils.stub_sections import _stub_section_for_pack

# Build brief object for stub generation
brief = ClientInputBrief(
    brand=BrandBrief(
        brand_name=client_brief.get("brand_name", "DemoCafe"),
        industry=client_brief.get("industry", "Coffee"),
        product_service=client_brief.get("unique_value", "Coffee"),
        primary_goal=client_brief.get("goal", "Growth"),
        primary_customer=client_brief.get("audience", "customers"),
    ),
    audience=AudienceBrief(primary_customer=client_brief.get("audience", "customers")),
    goal=GoalBrief(primary_goal=client_brief.get("goal", "Growth")),
    voice=VoiceBrief(tone_of_voice=[]),
    product_service=ProductServiceBrief(items=[]),
    assets_constraints=AssetsConstraintsBrief(focus_platforms=[]),
    operations=OperationsBrief(),
    strategy_extras=StrategyExtrasBrief(),
)

# Define section IDs for Quick Social (from package_presets.py)
QUICK_SOCIAL_SECTIONS = [
    "overview",
    "messaging_framework",
    "detailed_30_day_calendar",
    "content_buckets",
    "hashtag_strategy",
    "kpi_plan_light",
    "execution_roadmap",
    "final_summary",
]

# Generate sections directly from stub functions
print("⏳ Generating sections from stub functions...")
sections = []
for section_id in QUICK_SOCIAL_SECTIONS:
    content = _stub_section_for_pack("quick_social_basic", section_id, brief)
    if content:
        sections.append(
            {"id": section_id, "title": section_id.replace("_", " ").title(), "body": content}
        )
        print(f"✅ {section_id}: {len(content)} chars")
    else:
        print(f"❌ {section_id}: NO STUB")

print(f"\n✅ Generated {len(sections)} sections directly from stubs")

# ============================================================================
# STEP 2: Build Report Data Structure
# ============================================================================

print("\n📊 STEP 2: Building Report Data Structure")
print("-" * 80)

# Build report_data structure expected by build_pdf_context_for_wow_package
report_data = {
    "brand_name": client_brief["brand_name"],
    "campaign_title": "Quick Social Playbook",
    "primary_channel": "Instagram",
    "sections": sections,
}

print(f"✓ Report data structure built with {len(sections)} sections")

# ============================================================================
# STEP 3: Capture PDF Context
# ============================================================================

print("\n🎨 STEP 3: Building PDF Context")
print("-" * 80)

from backend.pdf_renderer import build_pdf_context_for_wow_package

context = build_pdf_context_for_wow_package(report_data, "quick_social_basic")

print(f"✓ Context built with {len(context)} fields")
print("\nContext Fields Analysis:")
print("-" * 80)

# Expected fields from QUICK_SOCIAL_SECTION_MAP
expected_fields = [
    "overview_html",
    "audience_segments_html",
    "messaging_framework_html",
    "content_buckets_html",
    "calendar_html",
    "creative_direction_html",
    "hashtags_html",
    "platform_guidelines_html",
    "kpi_plan_html",
    "final_summary_html",
]

for field in expected_fields:
    value = context.get(field, "")
    status = "✅ POPULATED" if value else "❌ EMPTY"
    preview = ""

    if value:
        # Clean HTML for preview
        clean_text = re.sub(r"<[^>]+>", "", value)  # Strip HTML tags
        clean_text = " ".join(clean_text.split())  # Normalize whitespace
        preview = clean_text[:150] + ("..." if len(clean_text) > 150 else "")

    print(f"\n{field}:")
    print(f"  Status: {status}")
    print(f"  Length: {len(value)} chars")
    if preview:
        print(f"  Preview: {preview}")

# Metadata fields
print("\n" + "=" * 80)
print("Metadata Fields:")
print(f"  brand_name: {context.get('brand_name')}")
print(f"  campaign_title: {context.get('campaign_title')}")
print(f"  primary_channel: {context.get('primary_channel')}")

# ============================================================================
# STEP 4: Generate PDF
# ============================================================================

print("\n" + "=" * 80)
print("📄 STEP 4: Generating PDF")
print("-" * 80)

from backend.export_utils import safe_export_agency_pdf

pdf_result = safe_export_agency_pdf(
    pack_key="quick_social_basic",
    report=report_data,
    wow_enabled=True,
    wow_package_key="quick_social_basic",
)

# safe_export_agency_pdf returns bytes directly, not a dict
if not pdf_result or len(pdf_result) == 0:
    print("❌ PDF generation returned empty bytes")
    sys.exit(1)

pdf_bytes = pdf_result
print(f"✅ PDF generated: {len(pdf_bytes):,} bytes")

# Save PDF
output_pdf = Path("/workspaces/AICMO/tmp_demo_quick_social_v2.pdf")
output_pdf.write_bytes(pdf_bytes)
print(f"✓ Saved to: {output_pdf}")

# ============================================================================
# STEP 5: Extract PDF Text
# ============================================================================

print("\n" + "=" * 80)
print("📝 STEP 5: Extracting PDF Text Content")
print("-" * 80)

pdf_text = ""
page_texts = []

# Try PyPDF2 first
try:
    from PyPDF2 import PdfReader

    reader = PdfReader(output_pdf)
    num_pages = len(reader.pages)
    print(f"✓ PDF has {num_pages} pages")

    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        page_texts.append({"page": page_num, "text": text})
        pdf_text += f"\n\n{'='*60}\nPAGE {page_num}\n{'='*60}\n\n{text}"

    print("✓ Extracted text using PyPDF2")

except ImportError:
    print("⚠️  PyPDF2 not available, trying pdftotext...")
    import subprocess

    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(output_pdf), "-"],
            capture_output=True,
            text=True,
            check=True,
        )
        pdf_text = result.stdout

        # Split by page breaks (rough approximation)
        page_splits = pdf_text.split("\f")
        for page_num, text in enumerate(page_splits, 1):
            if text.strip():
                page_texts.append({"page": page_num, "text": text})

        print(f"✓ Extracted text using pdftotext ({len(page_texts)} pages)")

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Could not extract text (no PyPDF2 or pdftotext available)")
        pdf_text = "[TEXT EXTRACTION UNAVAILABLE]"

# Save text dump
output_txt = Path("/workspaces/AICMO/tmp_demo_quick_social_v2.txt")
output_txt.write_text(pdf_text)
print(f"✓ Saved text dump to: {output_txt}")

# ============================================================================
# STEP 6: Page-by-Page Summary
# ============================================================================

print("\n" + "=" * 80)
print("📑 STEP 6: Page-by-Page Content Summary")
print("=" * 80)

for page_info in page_texts[:10]:  # Limit to first 10 pages
    page_num = page_info["page"]
    text = page_info["text"]

    # Extract first 400-500 chars
    preview = text[:500].strip()

    # Try to identify section by looking for headers
    lines = text.split("\n")
    headers = [
        line.strip()
        for line in lines
        if line.strip() and len(line.strip()) < 60 and line.strip().isupper() or ":" in line[:30]
    ]

    print(f"\n--- PAGE {page_num} ---")
    if headers:
        print(f"Detected Headers: {', '.join(headers[:3])}")
    print("Preview (first 500 chars):")
    print(preview)
    print()

# ============================================================================
# STEP 7: Summary Statistics
# ============================================================================

print("\n" + "=" * 80)
print("📊 FINAL SUMMARY")
print("=" * 80)

# Count populated fields
populated_count = sum(1 for field in expected_fields if context.get(field))
empty_count = len(expected_fields) - populated_count

print("\nContext Analysis:")
print(f"  Total expected fields: {len(expected_fields)}")
print(f"  Populated fields: {populated_count} ({populated_count/len(expected_fields)*100:.1f}%)")
print(f"  Empty fields: {empty_count} ({empty_count/len(expected_fields)*100:.1f}%)")

if empty_count > 0:
    print("\n  Empty fields:")
    for field in expected_fields:
        if not context.get(field):
            print(f"    - {field}")

print("\nPDF Output:")
print(f"  File size: {len(pdf_bytes):,} bytes")
print(f"  Pages: {len(page_texts)}")
print(f"  Text length: {len(pdf_text):,} characters")

# Quick heuristic: check if major sections appear in text
print("\nSection Presence Check (in PDF text):")
section_keywords = {
    "overview": ["overview", "social media overview"],
    "audience": ["audience", "reaching", "who you're"],
    "messaging": ["message", "messaging", "core message"],
    "content_buckets": ["content", "themes", "buckets"],
    "calendar": ["calendar", "schedule", "posting"],
    "creative": ["creative", "visual", "style"],
    "hashtags": ["hashtag"],
    "kpi": ["kpi", "metrics", "success"],
    "summary": ["summary", "next steps"],
}

for section, keywords in section_keywords.items():
    found = any(kw in pdf_text.lower() for kw in keywords)
    status = "✅" if found else "❌"
    print(f"  {status} {section}: {keywords[0]}")

print("\n" + "=" * 80)
print("✅ COMPARISON COMPLETE")
print("=" * 80)
print("\nOutput files:")
print(f"  PDF: {output_pdf}")
print(f"  Text: {output_txt}")
print("\nNext: Review PDF_COMPARISON_AUDIT_V2.md for detailed analysis")
