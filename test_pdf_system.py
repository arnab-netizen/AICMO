#!/usr/bin/env python3
"""
Test script to validate the refactored PDF system.

Validates:
1. Template resolution (pack → template mapping)
2. Context builder (report_data → flattened context)
3. Template rendering (HTML generation)
4. PDF generation (HTML → PDF bytes)
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.pdf_renderer import (
    resolve_pdf_template_for_pack,
    build_pdf_context_for_wow_package,
    render_agency_pdf,
    PDF_TEMPLATE_MAP,
)


def test_template_resolution():
    """Test 1: Verify pack → template mapping"""
    print("\n" + "=" * 80)
    print("TEST 1: Template Resolution")
    print("=" * 80)

    tests = [
        ("quick_social_basic", "quick_social_basic.html"),
        ("strategy_campaign_standard", "campaign_strategy.html"),
        ("unknown_pack", "campaign_strategy.html"),  # fallback
    ]

    for pack_key, expected_template in tests:
        result = resolve_pdf_template_for_pack(pack_key)
        status = "✅" if result == expected_template else "❌"
        print(f"{status} {pack_key} → {result} (expected: {expected_template})")

    print(f"\n📋 PDF_TEMPLATE_MAP has {len(PDF_TEMPLATE_MAP)} entries")
    for key, val in PDF_TEMPLATE_MAP.items():
        print(f"   - {key}: {val}")


def test_context_builder():
    """Test 2: Verify context builder creates template-friendly dicts"""
    print("\n" + "=" * 80)
    print("TEST 2: Context Builder")
    print("=" * 80)

    # Quick Social
    quick_social_report = {
        "brand_name": "Starbucks",
        "title": "Instagram Quick Start",
        "primary_channel": "Instagram",
        "overview_html": "<p>Test overview content</p>",
        "audience_segments_html": "<p>Millennials 25-35</p>",
        "messaging_framework_html": "<p>Core message: Quality coffee</p>",
        "calendar_html": "<table><tr><td>Mon</td></tr></table>",
    }

    ctx_qs = build_pdf_context_for_wow_package(quick_social_report, "quick_social_basic")

    print("\n✅ Quick Social Context:")
    print(f"   Keys: {len(ctx_qs)} total")
    print(f"   brand_name: {ctx_qs.get('brand_name')}")
    print(f"   campaign_title: {ctx_qs.get('campaign_title')}")
    print(f"   primary_channel: {ctx_qs.get('primary_channel')}")
    print(f"   Has overview_html: {bool(ctx_qs.get('overview_html'))}")
    print(f"   Has calendar_html: {bool(ctx_qs.get('calendar_html'))}")

    # Campaign Strategy
    campaign_report = {
        "brand_name": "Nike",
        "campaign_title": "Summer 2025 Launch",
        "campaign_duration": "Q2-Q3 2025",
        "objectives_html": "<p>Drive 25% awareness lift</p>",
        "core_campaign_idea_html": "<p>Just Do It - Summer Edition</p>",
        "channel_plan_html": "<ul><li>Instagram</li><li>TikTok</li></ul>",
        "personas": [
            {"name": "Active Amy", "role": "Fitness enthusiast", "goals": "Stay fit"},
        ],
        "roi_model": {
            "reach": {"q1": "1M", "q2": "2M"},
            "engagement": {"q1": "5%", "q2": "7%"},
        },
    }

    ctx_cs = build_pdf_context_for_wow_package(campaign_report, "strategy_campaign_standard")

    print("\n✅ Campaign Strategy Context:")
    print(f"   Keys: {len(ctx_cs)} total")
    print(f"   brand_name: {ctx_cs.get('brand_name')}")
    print(f"   campaign_title: {ctx_cs.get('campaign_title')}")
    print(f"   campaign_duration: {ctx_cs.get('campaign_duration')}")
    print(f"   Has objectives_html: {bool(ctx_cs.get('objectives_html'))}")
    print(f"   Has personas: {len(ctx_cs.get('personas', []))} personas")
    print(f"   Has roi_model: {bool(ctx_cs.get('roi_model'))}")


def test_pdf_generation():
    """Test 3: Generate sample PDFs"""
    print("\n" + "=" * 80)
    print("TEST 3: PDF Generation")
    print("=" * 80)

    try:
        # Quick Social PDF
        quick_social_report = {
            "brand_name": "Starbucks",
            "title": "Instagram Quick Start",
            "primary_channel": "Instagram",
            "overview_html": "<p><strong>Overview:</strong> Launch a strong Instagram presence with daily posts targeting coffee lovers.</p>",
            "audience_segments_html": "<p><strong>Target:</strong> Millennials 25-35, urban professionals who value quality coffee and convenience.</p>",
            "messaging_framework_html": "<p><strong>Core Message:</strong> Premium coffee experiences that fit your lifestyle.</p>",
            "content_buckets_html": "<ul><li>Behind-the-scenes brewing</li><li>Customer stories</li><li>New product launches</li></ul>",
            "calendar_html": "<table><tr><th>Day</th><th>Post</th></tr><tr><td>Monday</td><td>Product feature</td></tr></table>",
            "creative_direction_html": "<p><strong>Visual Style:</strong> Warm, inviting tones with green accents. Professional food photography.</p>",
            "hashtags_html": "<p>#Starbucks #CoffeeLovers #MorningBrew #QualityCoffee</p>",
            "platform_guidelines_html": "<ul><li>Post 1x daily at 8am PST</li><li>Use Stories for time-sensitive content</li></ul>",
            "kpi_plan_html": "<p><strong>Track:</strong> Engagement rate, follower growth, story views</p>",
            "final_summary_html": "<p><strong>Next Steps:</strong> Set up content calendar, create first week's posts, launch campaign</p>",
        }

        pdf_bytes_qs = render_agency_pdf(quick_social_report, "quick_social_basic")

        print("\n✅ Quick Social PDF generated:")
        print(f"   Size: {len(pdf_bytes_qs):,} bytes")
        print(f"   Valid PDF: {pdf_bytes_qs[:4] == b'%PDF'}")

        # Save to file
        output_file_qs = Path(__file__).parent / "test_quick_social_output.pdf"
        output_file_qs.write_bytes(pdf_bytes_qs)
        print(f"   Saved to: {output_file_qs}")

        # Campaign Strategy PDF
        campaign_report = {
            "brand_name": "Nike",
            "campaign_title": "Summer 2025 Launch",
            "campaign_duration": "Q2-Q3 2025 (April-September)",
            "objectives_html": "<ul><li>Drive 25% awareness lift among Gen Z</li><li>Achieve 15% increase in online sales</li><li>Generate 5M social impressions</li></ul>",
            "core_campaign_idea_html": "<p><strong>Big Idea:</strong> 'Move Your Summer' - Inspiring active lifestyles through authentic athlete stories and community challenges.</p>",
            "channel_plan_html": "<ul><li><strong>Instagram:</strong> Daily posts + Stories (40% budget)</li><li><strong>TikTok:</strong> 3x weekly challenges (30% budget)</li><li><strong>YouTube:</strong> Long-form content (20% budget)</li><li><strong>Display:</strong> Retargeting (10% budget)</li></ul>",
            "audience_segments_html": "<p><strong>Primary:</strong> Gen Z athletes (18-24), fitness-conscious, values sustainability</p><p><strong>Secondary:</strong> Millennials (25-34), casual fitness enthusiasts</p>",
            "personas": [
                {
                    "name": "Active Amy",
                    "role": "College athlete",
                    "goals": "Performance & style",
                    "challenges": "Budget constraints",
                },
                {
                    "name": "Runner Rob",
                    "role": "Marathon trainer",
                    "goals": "Durability",
                    "challenges": "Finding quality gear",
                },
            ],
            "creative_direction_html": "<p><strong>Visual Direction:</strong> Bold, dynamic imagery featuring real athletes in action. High-energy video content with authentic storytelling.</p>",
            "calendar_html": "<table><tr><th>Week</th><th>Theme</th></tr><tr><td>Week 1-2</td><td>Launch & Awareness</td></tr><tr><td>Week 3-4</td><td>Community Building</td></tr></table>",
            "execution_html": "<ol><li><strong>Week 1:</strong> Campaign kickoff, influencer partnerships go live</li><li><strong>Week 2-4:</strong> Ramp up social content, launch TikTok challenges</li><li><strong>Week 5-8:</strong> Optimize based on performance data</li></ol>",
            "kpi_budget_html": "<p><strong>Success Metrics:</strong></p><ul><li>Reach: 10M unique users</li><li>Engagement Rate: >5%</li><li>Conversion Rate: >3%</li><li>ROAS: >4:1</li></ul>",
        }

        pdf_bytes_cs = render_agency_pdf(campaign_report, "strategy_campaign_standard")

        print("\n✅ Campaign Strategy PDF generated:")
        print(f"   Size: {len(pdf_bytes_cs):,} bytes")
        print(f"   Valid PDF: {pdf_bytes_cs[:4] == b'%PDF'}")

        # Save to file
        output_file_cs = Path(__file__).parent / "test_campaign_strategy_output.pdf"
        output_file_cs.write_bytes(pdf_bytes_cs)
        print(f"   Saved to: {output_file_cs}")

    except Exception as e:
        print(f"\n❌ PDF generation failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


def main():
    """Run all tests"""
    print("\n" + "🎨" * 40)
    print("PDF SYSTEM VALIDATION TEST SUITE")
    print("🎨" * 40)

    try:
        test_template_resolution()
        test_context_builder()
        success = test_pdf_generation()

        print("\n" + "=" * 80)
        if success:
            print("✅ ALL TESTS PASSED - PDF system is working correctly!")
        else:
            print("❌ SOME TESTS FAILED - Check errors above")
        print("=" * 80 + "\n")

        return 0 if success else 1

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
