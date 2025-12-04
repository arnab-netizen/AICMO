#!/usr/bin/env python3
"""Test PDF with proper section parsing."""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from aicmo import api_aicmo_generate_report
from export import safe_export_agency_pdf

brief = {
    "brand_name": "DemoCafe",
    "brand_voice": "friendly, energetic",
    "industry": "Coffeehouse",
    "goal": "Boost footfall 25%",
    "audience": "Young professionals 25-40",
    "budget_range": "Under $5k/month",
    "competitors": "Local cafes, Starbucks",
    "channels": "Instagram, TikTok",
    "unique_value": "Locally roasted beans",
    "content_preferences": "Behind-the-scenes, latte art",
}

print("=" * 80)
print("Generating report...")
result = api_aicmo_generate_report(brief, "quick_social_basic", "draft")
md = result.get("report_markdown", "")
print(f"Generated {len(md)} chars")

print("\nParsing sections...")
parts = re.split(r"^## (.+?)$", md, flags=re.MULTILINE)
sections = []
for i in range(1, len(parts), 2):
    if i + 1 < len(parts):
        title = parts[i].strip()
        body = parts[i + 1].strip()
        sid = re.sub(r"[^a-z0-9_]", "", title.lower().replace(" ", "_").replace("&", "and"))
        sections.append({"id": sid, "title": title, "body": body})
        print(f"  {sid}: {len(body)} chars")

report_data = {
    "brand_name": brief["brand_name"],
    "campaign_title": "Quick Social Playbook",
    "primary_channel": "Instagram",
    "sections": sections,
}

print(f"\nGenerating PDF with {len(sections)} sections...")
pdf_result = safe_export_agency_pdf("quick_social_basic", report=report_data)
pdf_bytes = pdf_result.get("pdf_bytes")
print(f"Generated {len(pdf_bytes)} bytes")

path = "/workspaces/AICMO/tmp_test_sections.pdf"
open(path, "wb").write(pdf_bytes)
print(f"\nSaved to: {path}")
print(f"Size: {len(pdf_bytes)} bytes")
print("🎉 SUCCESS!" if len(pdf_bytes) > 20000 else "⚠️  Still small")
print("=" * 80)
