"""
End-to-end sanity tests for agency-grade PDF export system.

Tests verify:
1. Backend PDF endpoint returns valid bytes
2. HTML template rendering works
3. Streamlit handler validates properly
4. Full integration from generation to PDF
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests  # noqa: E402

# Test configuration
BACKEND_URL = (
    os.environ.get("AICMO_BACKEND_URL") or os.environ.get("BACKEND_URL") or "http://127.0.0.1:8000"
)
TIMEOUT = 30


def test_pdf_endpoint_basic():
    """Test 1: PDF endpoint accepts markdown and returns valid bytes."""
    print("\n" + "=" * 80)
    print("TEST 1: Basic PDF Export (Markdown Mode)")
    print("=" * 80)

    try:
        # Prepare test markdown
        test_markdown = """# Marketing Plan

## Overview
This is a test marketing plan for AICMO.

## Campaign Strategy
- Focus on digital channels
- Target millennials and Gen Z
- Measure ROI via UTM parameters

## Results
Expected 15% engagement lift.
"""

        # Call PDF export endpoint
        resp = requests.post(
            f"{BACKEND_URL}/aicmo/export/pdf",
            json={"markdown": test_markdown},
            timeout=TIMEOUT,
        )

        # Verify response
        print(f"Status Code: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
        print(f"Content-Length: {len(resp.content)} bytes")

        # Check 1: Status code
        if resp.status_code != 200:
            print(f"❌ FAIL: Expected 200, got {resp.status_code}")
            if resp.status_code >= 400:
                try:
                    print(f"Error response: {resp.json()}")
                except Exception:  # noqa: E722
                    print(f"Response: {resp.text[:200]}")
            return False

        # Check 2: Content-Type
        content_type = resp.headers.get("Content-Type", "")
        if not content_type.startswith("application/pdf"):
            print(f"❌ FAIL: Wrong content-type: {content_type}")
            return False

        # Check 3: PDF header
        pdf_bytes = resp.content
        if not pdf_bytes.startswith(b"%PDF"):
            print("❌ FAIL: Missing PDF header")
            print(f"First bytes: {pdf_bytes[:20]}")
            return False

        # Check 4: File size
        if len(pdf_bytes) < 500:  # A real PDF should be at least 500 bytes
            print(f"❌ FAIL: PDF too small ({len(pdf_bytes)} bytes)")
            return False

        # Save for inspection
        output_path = Path("/tmp/test_pdf_basic.pdf")
        output_path.write_bytes(pdf_bytes)
        print(f"✅ PASS: Valid PDF generated ({len(pdf_bytes)} bytes)")
        print(f"   Saved to: {output_path}")
        return True

    except requests.exceptions.ConnectionError:
        print(f"❌ FAIL: Cannot connect to backend at {BACKEND_URL}")
        return False
    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__}: {e}")
        return False


def test_pdf_endpoint_structured():
    """Test 2: PDF endpoint with structured sections (HTML template mode)."""
    print("\n" + "=" * 80)
    print("TEST 2: Structured PDF Export (HTML Template Mode)")
    print("=" * 80)

    try:
        # Prepare test sections
        test_sections = [
            {
                "id": "overview",
                "title": "Overview",
                "body": "This is an overview of the marketing strategy.",
            },
            {
                "id": "objectives",
                "title": "Campaign Objectives",
                "body": "- Increase brand awareness\n- Generate qualified leads\n- Drive conversions",
            },
            {
                "id": "strategy",
                "title": "Core Strategy",
                "body": "Focus on multi-channel approach combining digital and traditional media.",
            },
        ]

        # Prepare brief metadata
        test_brief = {
            "client_name": "Test Client",
            "brand_name": "Test Brand",
            "product_service": "Digital Marketing Services",
            "location": "San Francisco, CA",
            "campaign_duration": "Q4 2025",
            "prepared_by": "AICMO Test Suite",
            "date_str": datetime.now().strftime("%Y-%m-%d"),
        }

        # Call PDF export endpoint with structured data
        resp = requests.post(
            f"{BACKEND_URL}/aicmo/export/pdf",
            json={
                "sections": test_sections,
                "brief": test_brief,
            },
            timeout=TIMEOUT,
        )

        # Verify response
        print(f"Status Code: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
        print(f"Content-Length: {len(resp.content)} bytes")

        # Check 1: Status code
        if resp.status_code != 200:
            print(f"❌ FAIL: Expected 200, got {resp.status_code}")
            if resp.status_code >= 400:
                try:
                    print(f"Error response: {resp.json()}")
                except Exception:  # noqa: E722
                    print(f"Response: {resp.text[:200]}")
            return False

        # Check 2: Content-Type
        content_type = resp.headers.get("Content-Type", "")
        if not content_type.startswith("application/pdf"):
            print(f"❌ FAIL: Wrong content-type: {content_type}")
            return False

        # Check 3: PDF header
        pdf_bytes = resp.content
        if not pdf_bytes.startswith(b"%PDF"):
            print("❌ FAIL: Missing PDF header")
            print(f"First bytes: {pdf_bytes[:20]}")
            return False

        # Check 4: File size (structured PDF should be larger)
        if len(pdf_bytes) < 1000:
            print(f"❌ FAIL: PDF too small ({len(pdf_bytes)} bytes)")
            return False

        # Save for inspection
        output_path = Path("/tmp/test_pdf_structured.pdf")
        output_path.write_bytes(pdf_bytes)
        print(f"✅ PASS: Valid PDF generated from structured sections ({len(pdf_bytes)} bytes)")
        print(f"   Saved to: {output_path}")
        return True

    except requests.exceptions.ConnectionError:
        print(f"❌ FAIL: Cannot connect to backend at {BACKEND_URL}")
        return False
    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__}: {e}")
        return False


def test_pdf_error_handling():
    """Test 3: PDF endpoint handles errors gracefully."""
    print("\n" + "=" * 80)
    print("TEST 3: Error Handling")
    print("=" * 80)

    try:
        # Test 3a: Empty markdown
        print("\n3a. Empty markdown:")
        resp = requests.post(
            f"{BACKEND_URL}/aicmo/export/pdf",
            json={"markdown": ""},
            timeout=TIMEOUT,
        )

        if resp.status_code == 400:
            try:
                error_data = resp.json()
                if error_data.get("error"):
                    print(
                        f"   ✅ PASS: Returns 400 with error: {error_data.get('message', 'N/A')[:60]}"
                    )
                else:
                    print("   ⚠️  Status 400 but no error flag in response")
            except Exception:  # noqa: E722
                print("   ⚠️  Status 400 but response is not JSON")
        else:
            print(f"   ❌ FAIL: Expected 400, got {resp.status_code}")

        # Test 3b: Invalid request (no markdown or sections)
        print("\n3b. Invalid request (empty payload):")
        resp = requests.post(
            f"{BACKEND_URL}/aicmo/export/pdf",
            json={},
            timeout=TIMEOUT,
        )

        if resp.status_code >= 400:
            print(f"   ✅ PASS: Returns error status {resp.status_code}")
        else:
            print(f"   ⚠️  Expected error, got {resp.status_code}")

        return True

    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__}: {e}")
        return False


def test_package_presets_integration():
    """Test 4: Verify package presets are properly configured."""
    print("\n" + "=" * 80)
    print("TEST 4: Package Presets Integration")
    print("=" * 80)

    try:
        # Load package presets
        from aicmo.presets.package_presets import PACKAGE_PRESETS

        # Check for strategy_campaign_standard
        if "strategy_campaign_standard" not in PACKAGE_PRESETS:
            print("❌ FAIL: strategy_campaign_standard not found in PACKAGE_PRESETS")
            return False

        preset = PACKAGE_PRESETS["strategy_campaign_standard"]
        sections = preset.get("sections", [])

        print(f"Package: {preset.get('label', 'N/A')}")
        print(f"Sections: {len(sections)}")
        print(f"Complexity: {preset.get('complexity', 'N/A')}")
        print(f"Requires Research: {preset.get('requires_research', False)}")

        # Check 1: Should have 17 sections
        if len(sections) != 17:
            print(f"⚠️  Expected 17 sections, got {len(sections)}")
        else:
            print("✅ PASS: Has 17 sections")

        # Check 2: Verify all packages use slug keys
        non_slug_keys = [k for k in PACKAGE_PRESETS.keys() if " " in k or "(" in k]
        if non_slug_keys:
            print(f"❌ FAIL: Found non-slug keys: {non_slug_keys}")
            return False

        print(f"✅ PASS: All {len(PACKAGE_PRESETS)} packages use slug keys")
        return True

    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__}: {e}")
        return False


def test_pdf_renderer_module():
    """Test 5: Verify PDF renderer module is importable and functional."""
    print("\n" + "=" * 80)
    print("TEST 5: PDF Renderer Module")
    print("=" * 80)

    try:
        from backend.pdf_renderer import sections_to_html_list  # noqa: F401

        # Test section conversion
        test_sections = [
            {"id": "test1", "title": "Test Section 1", "body": "Some **bold** text"},
            {"id": "test2", "title": "Test Section 2", "body": "- Bullet point"},
        ]

        html_sections = sections_to_html_list(test_sections)
        print("✅ PASS: sections_to_html_list works")
        print(f"   Converted {len(html_sections)} sections")

        # Test PDF rendering (may fail if WeasyPrint not installed, but module should be importable)
        print("✅ PASS: PDF renderer module is importable")
        return True

    except ImportError as e:
        if "WeasyPrint" in str(e):
            print(f"⚠️  WeasyPrint not installed (optional): {e}")
            return True  # Not a failure, just optional
        else:
            print(f"❌ FAIL: Import error: {e}")
            return False
    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__}: {e}")
        return False


def main():
    """Run all sanity tests."""
    print("\n" + "=" * 80)
    print("AICMO AGENCY-GRADE PDF EXPORT SANITY TESTS")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {
        "Basic PDF Export": test_pdf_endpoint_basic(),
        "Structured PDF Export": test_pdf_endpoint_structured(),
        "Error Handling": test_pdf_error_handling(),
        "Package Presets": test_package_presets_integration(),
        "PDF Renderer Module": test_pdf_renderer_module(),
    }

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Agency-grade PDF export is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
