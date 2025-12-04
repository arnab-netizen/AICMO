#!/usr/bin/env python3
"""
Generic dev script to generate PDF for ANY WOW pack using stub sections.

Usage:
    python scripts/dev_compare_pdf_for_pack.py --pack quick_social_basic
    python scripts/dev_compare_pdf_for_pack.py --pack strategy_campaign_standard
    python scripts/dev_compare_pdf_for_pack.py --pack full_funnel_growth_suite
    
Outputs PDF to: tmp_demo_{pack_key}.pdf
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from aicmo.presets.package_presets import PACKAGE_PRESETS
from backend.utils.stub_sections import _stub_section_for_pack
from backend.pdf_renderer import render_agency_pdf


def generate_stub_report_for_pack(pack_key: str) -> dict:
    """Generate a full report structure using stub sections for the given pack."""

    # Get pack configuration
    pack_config = PACKAGE_PRESETS.get(pack_key)
    if not pack_config:
        raise ValueError(f"Unknown pack: {pack_key}")

    # Mock brief for stub generation
    brief = {
        "brand_name": "ACME Corporation",
        "industry": "Technology",
        "target_audience": "Tech-savvy professionals aged 25-45",
        "primary_goal": "Increase brand awareness and drive conversions",
        "campaign_duration": "90 days",
        "budget_range": "$50,000 - $100,000",
        "primary_channel": "Instagram",
        "secondary_channels": ["Facebook", "LinkedIn", "TikTok"],
    }

    # Generate sections from stubs
    sections = []
    section_ids = pack_config["sections"]

    print(f"\n🎯 Generating {len(section_ids)} stub sections for pack: {pack_key}")
    print(f"   Sections: {', '.join(section_ids)}\n")

    for section_id in section_ids:
        content = _stub_section_for_pack(pack_key, section_id, brief)
        if content:
            sections.append(
                {"id": section_id, "title": section_id.replace("_", " ").title(), "body": content}
            )
            print(f"   ✓ {section_id}: {len(content)} chars")
        else:
            print(f"   ⚠️  {section_id}: NO STUB (empty content)")
            # Create minimal stub even if function returns None
            sections.append(
                {
                    "id": section_id,
                    "title": section_id.replace("_", " ").title(),
                    "body": f"[{section_id} - placeholder content]",
                }
            )

    # Build report structure
    report = {
        "sections": sections,
        "metadata": {
            "brand_name": brief["brand_name"],
            "industry": brief["industry"],
            "campaign_title": f"{brief['brand_name']} {pack_config['label']}",
            "campaign_duration": brief.get("campaign_duration", "90 days"),
            "primary_channel": brief.get("primary_channel", "Instagram"),
        },
    }

    return report


def main():
    parser = argparse.ArgumentParser(description="Generate PDF for any WOW pack using stubs")
    parser.add_argument(
        "--pack",
        type=str,
        required=True,
        help="Pack key (e.g., quick_social_basic, strategy_campaign_standard)",
    )
    args = parser.parse_args()

    pack_key = args.pack

    # Validate pack exists
    if pack_key not in PACKAGE_PRESETS:
        print(f"❌ Unknown pack: {pack_key}")
        print(f"   Available packs: {', '.join(PACKAGE_PRESETS.keys())}")
        return 1

    # Generate stub report
    try:
        report = generate_stub_report_for_pack(pack_key)
    except Exception as e:
        print(f"❌ Error generating stub report: {e}")
        return 1

    # Generate PDF
    output_path = f"tmp_demo_{pack_key}.pdf"
    print(f"\n📄 Generating PDF: {output_path}")

    try:
        pdf_bytes = render_agency_pdf(
            report_data=report,
            wow_package_key=pack_key,
        )

        if not pdf_bytes:
            print("❌ PDF generation returned empty bytes")
            return 1

        # Write to file
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        # Get file size
        file_size = os.path.getsize(output_path)
        file_size_kb = file_size / 1024

        print("\n✅ PDF generated successfully!")
        print(f"   File: {output_path}")
        print(f"   Size: {file_size_kb:.1f} KB ({file_size:,} bytes)")
        print(f"   Sections generated: {len(report['sections'])}")

        # Try to count pages using pdfinfo or similar
        try:
            import PyPDF2

            with open(output_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                page_count = len(pdf_reader.pages)
                print(f"   Pages: {page_count}")
        except Exception:
            print("   Pages: (install PyPDF2 to count pages)")

        return 0

    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
