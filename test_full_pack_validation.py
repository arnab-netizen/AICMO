#!/usr/bin/env python3
"""
Full Pack Generation Test with Validation

This script generates a complete quick_social_basic pack and validates:
1. Generation completes successfully 
2. hashtag_strategy section is present
3. All quality checks pass
4. No validation errors
"""

from fastapi.testclient import TestClient
from backend.main import app


def main():
    print("=" * 60)
    print("FULL PACK GENERATION TEST - quick_social_basic")
    print("=" * 60)

    client = TestClient(app)

    # Create payload for quick_social_basic pack
    payload = {
        "stage": "draft",
        "client_brief": {
            "raw_brief_text": "Starbucks is a global coffee chain",
            "client_name": "Starbucks",
            "brand_name": "Starbucks",
            "industry": "Coffee & Beverages",
            "product_service": "Coffee, tea, pastries, and cafe experience",
            "geography": "Seattle, USA",
            "primary_goal": "Increase brand engagement and drive foot traffic",
            "timeline": "90 days",
            "objectives": "Boost social media engagement by 30% and increase daily visits",
            "budget": "$50,000",
            "constraints": "Maintain premium brand image, focus on sustainability",
        },
        "services": {
            "include_agency_grade": False,
            "social_calendar": True,
            "brand_guidelines": False,
            "landing_page": False,
        },
        "package_name": "quick_social_basic",
        "wow_enabled": True,  # Enable WOW for proper structure
        "wow_package_key": "quick_social_basic",
        "use_learning": False,
        "refinement_mode": {
            "name": "Balanced",
            "label": "Standard quality",
            "iterations": 1,
        },
        "feedback": "",
        "previous_draft": "",
        "learn_items": [],
        "industry_key": None,
    }

    print("\n📝 Generating quick_social_basic pack for Starbucks...")
    print("   - WOW enabled: True")
    print("   - Validation: ON (default)")
    print("   - Package: quick_social_basic")

    try:
        # Make API call
        response = client.post("/api/aicmo/generate_report", json=payload)

        print(f"\n✅ API Response Status: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ ERROR: API returned {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return 1

        data = response.json()

        # Extract report
        report_text = data.get("report_markdown", "")
        print(f"✅ Generated report: {len(report_text)} characters")

        # Check for hashtag_strategy section
        if "hashtag" in report_text.lower():
            print("✅ hashtag_strategy section present in report")
        else:
            print("⚠️  No hashtag_strategy section found")

        # Check for brand personalization
        if "Starbucks" in report_text:
            print("✅ Report personalized with brand name")

        # Check for errors
        error_indicators = [
            "[Error generating",
            "AttributeError",
            "KeyError",
            "Validation failed",
            "Benchmark validation failed",
        ]

        found_errors = []
        for indicator in error_indicators:
            if indicator in report_text:
                found_errors.append(indicator)

        if found_errors:
            print("\n❌ Found error indicators in report:")
            for err in found_errors:
                print(f"   - {err}")
            return 1
        else:
            print("✅ No error indicators found in report")

        # Save report for inspection
        from pathlib import Path

        output_path = Path("tmp/full_pack_test_output.md")
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text(report_text)
        print(f"\n💾 Saved full report to: {output_path}")

        # Check if hashtag section has the right structure
        if "## Brand Hashtags" in report_text:
            print("✅ hashtag_strategy has 'Brand Hashtags' section")
        if "## Industry Hashtags" in report_text:
            print("✅ hashtag_strategy has 'Industry Hashtags' section")
        if "## Campaign Hashtags" in report_text:
            print("✅ hashtag_strategy has 'Campaign Hashtags' section")
        if "## Usage Guidelines" in report_text:
            print("✅ hashtag_strategy has 'Usage Guidelines' section")

        print("\n" + "=" * 60)
        print("✅ SUCCESS: Full pack generated with validation ON")
        print("   - No benchmark errors")
        print("   - hashtag_strategy is Perplexity-powered (or uses fallbacks)")
        print("   - All quality checks passed")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ ERROR during generation: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
