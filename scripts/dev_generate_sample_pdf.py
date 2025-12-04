#!/usr/bin/env python3
"""
Development Script: Generate Sample PDF for Verification

Purpose:
    Generate a real PDF file from AICMO's Quick Social Pack
    to verify the PDF pipeline outputs correctly.

Usage:
    cd /workspaces/AICMO
    python scripts/dev_generate_sample_pdf.py

Output:
    Creates tmp_demo_quick_social.pdf in repo root

DO NOT use in production. Dev/test only.
"""

import os
import sys
import re

# Set dev-safe environment variables BEFORE imports
os.environ.setdefault("AICMO_STUB_MODE", "1")
os.environ.setdefault("AICMO_USE_LLM", "0")
os.environ.setdefault("AICMO_PERPLEXITY_ENABLED", "0")
os.environ.setdefault("AICMO_ENABLE_HTTP_LEARNING", "0")
os.environ.setdefault("AICMO_SKIP_QUALITY_GATE", "1")  # Skip validation for PDF test

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
from pathlib import Path


def make_sample_brief_dict() -> dict:
    """
    Create a realistic sample brief dict for testing.

    Returns dict matching Streamlit payload format (not ClientInputBrief object).
    """
    return {
        "brand_name": "DemoCafe",
        "industry": "Coffeehouse / Beverage Retail",
        "product_service": "Specialty coffee, organic teas, and artisan pastries",
        "primary_goal": "Boost in-store footfall by 25% and increase Instagram engagement by 40%",
        "primary_customer": "Urban professionals aged 25-40 who value quality and convenience",
        "geography": "Kolkata, India",
        "timeline": "30 days",
        "objectives": "Increase brand awareness and drive store visits",
        "budget": "₹50,000 for ads and content production",
        "pain_points": [
            "Finding consistent quality coffee nearby",
            "Long wait times at popular cafes",
        ],
        "kpis": ["store visit count", "Instagram saves", "DM inquiries", "hashtag reach"],
    }


async def main():
    """Main execution function."""
    print("=" * 80)
    print("🎨 PDF GENERATION TEST - Quick Social Pack")
    print("=" * 80)

    # Import after env vars set
    from backend.main import api_aicmo_generate_report
    from backend.export_utils import safe_export_agency_pdf

    # STEP 1: Build payload for quick_social_basic pack
    client_brief = make_sample_brief_dict()

    payload = {
        "stage": "draft",
        "client_brief": client_brief,
        "services": {
            "include_agency_grade": False,  # Keep it simple for PDF test
        },
        "pack_key": "quick_social_basic",
        "wow_enabled": False,  # Disable WOW to skip quality gate for PDF test
        "wow_package_key": None,
        "use_learning": False,
        "industry_key": "food_beverage",
    }

    print(f"\n✅ Step 1: Created payload for pack '{payload['pack_key']}'")
    print(f"   Brand: {client_brief['brand_name']}")
    print(f"   Industry: {client_brief['industry']}")
    print(f"   Goal: {client_brief['primary_goal'][:60]}...")

    # STEP 2: Generate report via main endpoint
    print("\n🔄 Step 2: Generating report via api_aicmo_generate_report()...")

    try:
        result = await api_aicmo_generate_report(payload)

        if not result or result.get("status") != "success":
            print(f"❌ Report generation failed: {result}")
            return 1

        print("✅ Report generated successfully")
        print(f"   Markdown length: {len(result.get('report_markdown', ''))} chars")
        print(f"   Status: {result.get('status')}")

    except Exception as e:
        print(f"❌ Report generation failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return 1

    # STEP 3: Extract report dict for PDF rendering
    # The result should contain the full report structure
    print("\n🔄 Step 3: Extracting report data for PDF rendering...")

    # The report dict is embedded in the result
    # We need to extract it properly - check what's actually returned
    report_data = result.get("report", {})

    if not report_data:
        print("⚠️  WARNING: No 'report' dict in result, parsing markdown instead")
        # Build report dict from markdown
        report_markdown = result.get("report_markdown", "")
        print("   Markdown preview (first 300 chars):")
        print(f"   {report_markdown[:300]}")

        # Parse markdown into sections
        parts = re.split(r"##\s+(?:\d+\.\s+)?(.+?)$", report_markdown, flags=re.MULTILINE)
        print(f"   Split result: {len(parts)} parts")
        sections = []
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                title = parts[i].strip()
                body = parts[i + 1].strip()
                section_id = re.sub(
                    r"[^a-z0-9_]", "", title.lower().replace(" ", "_").replace("&", "and")
                )
                sections.append({"id": section_id, "title": title, "body": body})
                print(f"   Parsed section TITLE: '{title}'")
                print(f"   Parsed section ID: {section_id} ({len(body)} chars)")

        report_data = {
            "brand_name": client_brief["brand_name"],
            "campaign_title": "Quick Social Playbook",
            "primary_channel": "Instagram",
            "sections": sections,
        }
        print(f"   Total sections: {len(sections)}")

        # Try to extract HTML sections if available
        if sections:
            print(f"   Found {len(sections)} sections in result")
            # Map section IDs to _html fields expected by template
            section_map = {
                "overview": "overview_html",
                "audience_segments": "audience_segments_html",
                "messaging_framework": "messaging_framework_html",
                "content_buckets": "content_buckets_html",
                "detailed_30_day_calendar": "calendar_html",
                "creative_direction": "creative_direction_html",
                "hashtag_strategy": "hashtags_html",
                "platform_guidelines": "platform_guidelines_html",
                "kpi_plan_light": "kpi_plan_html",
                "final_summary": "final_summary_html",
            }

            for section in sections:
                section_id = section.get("id")
                html_key = section_map.get(section_id)
                if html_key:
                    # Convert markdown to HTML (simple approach)
                    body_md = section.get("body", "")
                    try:
                        import markdown

                        body_html = markdown.markdown(body_md)
                    except ImportError:
                        # Fallback: wrap in <p> tags
                        body_html = f"<p>{body_md}</p>"

                    report_data[html_key] = body_html
                    print(f"   ✓ Mapped section '{section_id}' to '{html_key}'")

    print(f"   Report data keys: {list(report_data.keys())}")

    # STEP 4: Generate PDF using agency PDF renderer
    print("\n🔄 Step 4: Rendering PDF via safe_export_agency_pdf()...")

    try:
        pdf_bytes = safe_export_agency_pdf(
            pack_key="quick_social_basic",
            report=report_data,
            wow_enabled=True,  # Force agency PDF path even though WOW generation was disabled
            wow_package_key="quick_social_basic",
        )

        if not pdf_bytes:
            print("❌ PDF generation returned None (agency path failed)")
            print("   This means the agency PDF renderer couldn't generate the PDF")
            print("   Possible causes:")
            print("   - WeasyPrint not available")
            print("   - Template not found")
            print("   - Context data missing required fields")
            return 1

        print(f"✅ PDF generated successfully: {len(pdf_bytes)} bytes")

    except Exception as e:
        print(f"❌ PDF generation failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return 1

    # STEP 5: Write PDF to file
    output_path = Path("/workspaces/AICMO/tmp_demo_quick_social.pdf")

    print(f"\n🔄 Step 5: Writing PDF to {output_path}...")

    try:
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        print(f"✅ PDF written successfully: {output_path}")
        print(f"   File size: {output_path.stat().st_size} bytes")
        print(f"\n📄 To view the PDF, open: {output_path}")

    except Exception as e:
        print(f"❌ Failed to write PDF file: {e}")
        import traceback

        traceback.print_exc()
        return 1

    print("\n" + "=" * 80)
    print("✅ PDF GENERATION TEST COMPLETE")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
