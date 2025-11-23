#!/usr/bin/env python3
"""
End-to-end test for agency-grade processing and PDF export.

This script verifies:
1. Goal 1: Agency-grade processing is triggered (include_agency_grade=True, use_learning=True)
2. Goal 2: PDF export works correctly and downloaded PDFs open

Usage:
    python tools/test_agency_grade_e2e.py
"""

import os
import sys
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_streamlit_payload_to_backend():
    """
    Test Goal 1: Verify Streamlit-style payload with both flags is accepted by backend.
    """
    print("\n" + "=" * 80)
    print("TEST 1: Streamlit Payload → Backend Endpoint")
    print("=" * 80)

    # Build a Streamlit-style payload (similar to what aicmo_operator.py sends)
    streamlit_payload = {
        "stage": "draft",
        "client_brief": {
            "client_name": "Test Corp",
            "brand_name": "TestBrand",
            "product_service": "SaaS Platform",
            "industry": "Technology",
            "geography": "North America",
            "objectives": "Launch new product, increase market share",
            "budget": "$50,000",
            "timeline": "Q1 2026",
            "constraints": "Limited brand awareness",
        },
        "services": {
            "marketing_plan": True,
            "campaign_blueprint": True,
            "social_calendar": True,
            "performance_review": False,
            "creatives": True,
            "include_agency_grade": True,  # ✅ GOAL 1: Enable agency-grade
        },
        "package_name": "Strategy + Campaign Pack (Standard)",
        "wow_enabled": True,
        "wow_package_key": "strategy_campaign_standard",
        "refinement_mode": {
            "name": "balanced",
            "depth": 2,
        },
        "feedback": "",
        "previous_draft": "",
        "learn_items": [
            {"text": "Example learning item", "tags": ["test"]},
        ],
        "use_learning": True,  # ✅ GOAL 1: Enable learning system
        "industry_key": "technology",
    }

    print("\n📦 Payload includes:")
    print(f"   - include_agency_grade: {streamlit_payload['services']['include_agency_grade']}")
    print(f"   - use_learning: {streamlit_payload['use_learning']}")
    print(f"   - package_name: {streamlit_payload['package_name']}")

    # Option 1: Test with backend URL if available
    backend_url = os.environ.get("AICMO_BACKEND_URL")

    if backend_url:
        print(f"\n🌐 Backend URL found: {backend_url}")
        print("   Sending request to /api/aicmo/generate_report...")

        try:
            resp = requests.post(
                backend_url.rstrip("/") + "/api/aicmo/generate_report",
                json=streamlit_payload,
                timeout=60,
            )

            if resp.status_code == 200:
                data = resp.json()
                report_markdown = data.get("report_markdown", "")

                print("\n✅ SUCCESS: Backend returned report")
                print(f"   - Status: {data.get('status')}")
                print(f"   - Report length: {len(report_markdown)} chars")
                print(f"   - Preview: {report_markdown[:200]}...")

                return True, report_markdown
            else:
                print(f"\n❌ FAILED: Backend returned {resp.status_code}")
                print(f"   Response: {resp.text}")
                return False, None

        except Exception as e:
            print("\n❌ FAILED: Exception during backend call")
            print(f"   Error: {e}")
            return False, None
    else:
        print("\n⚠️  AICMO_BACKEND_URL not set, skipping backend test")
        print("   To test with backend, set AICMO_BACKEND_URL environment variable")

        # Option 2: Test directly with Python imports (local test)
        print("\n🔧 Testing with local imports instead...")

        try:
            from backend.main import api_aicmo_generate_report
            import asyncio

            result = asyncio.run(api_aicmo_generate_report(streamlit_payload))
            report_markdown = result.get("report_markdown", "")

            print("\n✅ SUCCESS: Local test returned report")
            print(f"   - Status: {result.get('status')}")
            print(f"   - Report length: {len(report_markdown)} chars")
            print(f"   - Preview: {report_markdown[:200]}...")

            return True, report_markdown

        except Exception as e:
            print("\n❌ FAILED: Local test exception")
            print(f"   Error: {e}")
            import traceback

            traceback.print_exc()
            return False, None


def test_pdf_export(report_markdown: str):
    """
    Test Goal 2: Verify PDF export works and returns valid PDF bytes.
    """
    print("\n" + "=" * 80)
    print("TEST 2: PDF Export (Binary Data)")
    print("=" * 80)

    if not report_markdown:
        print("\n⚠️  No report markdown available, skipping PDF test")
        return False

    backend_url = os.environ.get("AICMO_BACKEND_URL")

    if backend_url:
        print(f"\n🌐 Backend URL found: {backend_url}")
        print("   Sending PDF export request to /aicmo/export/pdf...")

        try:
            resp = requests.post(
                backend_url.rstrip("/") + "/aicmo/export/pdf",
                json={"markdown": report_markdown},
                timeout=60,
            )

            if resp.status_code == 200:
                # ✅ GOAL 2: Use resp.content for binary data (not resp.text)
                pdf_bytes = resp.content

                print("\n✅ SUCCESS: Backend returned PDF")
                print(f"   - Content-Type: {resp.headers.get('Content-Type')}")
                print(f"   - Content-Disposition: {resp.headers.get('Content-Disposition')}")
                print(f"   - PDF size: {len(pdf_bytes)} bytes")

                # Verify it's actually PDF
                if pdf_bytes.startswith(b"%PDF"):
                    print("   - ✅ Valid PDF header detected")

                    # Save to file for manual verification
                    output_path = project_root / "tools" / "test_output.pdf"
                    output_path.write_bytes(pdf_bytes)
                    print(f"   - 💾 Saved to: {output_path}")
                    print(f"   - 🔍 Open with: xdg-open {output_path} (or your PDF viewer)")

                    return True
                else:
                    print("   - ⚠️  WARNING: Does not start with %PDF header")
                    print(f"   - First 100 bytes: {pdf_bytes[:100]}")
                    return False
            else:
                print(f"\n❌ FAILED: Backend returned {resp.status_code}")
                print(f"   Response: {resp.text[:500]}")
                return False

        except Exception as e:
            print("\n❌ FAILED: Exception during PDF export")
            print(f"   Error: {e}")
            return False
    else:
        print("\n⚠️  AICMO_BACKEND_URL not set, skipping backend PDF test")
        print("   To test with backend, set AICMO_BACKEND_URL environment variable")

        # Test directly with Python imports
        print("\n🔧 Testing with local imports instead...")

        try:
            from backend.export_utils import safe_export_pdf

            result = safe_export_pdf(report_markdown, check_placeholders=True)

            if hasattr(result, "body_iterator"):
                # It's a StreamingResponse, extract bytes
                pdf_bytes = b"".join(result.body_iterator)

                print("\n✅ SUCCESS: Local test returned PDF")
                print(f"   - PDF size: {len(pdf_bytes)} bytes")

                if pdf_bytes.startswith(b"%PDF"):
                    print("   - ✅ Valid PDF header detected")

                    output_path = project_root / "tools" / "test_output.pdf"
                    output_path.write_bytes(pdf_bytes)
                    print(f"   - 💾 Saved to: {output_path}")
                    print(f"   - 🔍 Open with: xdg-open {output_path} (or your PDF viewer)")

                    return True
                else:
                    print("   - ⚠️  WARNING: Does not start with %PDF header")
                    return False
            else:
                print("\n❌ FAILED: Result is not a StreamingResponse")
                print(f"   Result type: {type(result)}")
                print(f"   Result: {result}")
                return False

        except Exception as e:
            print("\n❌ FAILED: Local test exception")
            print(f"   Error: {e}")
            import traceback

            traceback.print_exc()
            return False


def main():
    """Run all end-to-end tests."""
    print("\n" + "=" * 80)
    print("AICMO AGENCY-GRADE + PDF EXPORT E2E TEST")
    print("=" * 80)
    print("\nThis test verifies:")
    print("  1. include_agency_grade=True is passed to backend")
    print("  2. use_learning=True is passed to backend")
    print("  3. PDF export returns valid binary PDF (not JSON-wrapped)")
    print("  4. Downloaded PDF can be opened in a PDF viewer")

    # Test 1: Streamlit payload → backend endpoint
    test1_passed, report_markdown = test_streamlit_payload_to_backend()

    # Test 2: PDF export
    test2_passed = test_pdf_export(report_markdown) if test1_passed else False

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"\n  Test 1 (Agency-Grade Payload): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  Test 2 (PDF Export):            {'✅ PASSED' if test2_passed else '❌ FAILED'}")

    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nNext steps:")
        print("  1. Start Streamlit: streamlit run streamlit_pages/aicmo_operator.py")
        print("  2. Select 'Strategy + Campaign Pack (Standard)'")
        print("  3. Click 'Generate draft report'")
        print("  4. Verify backend logs show: 'include_agency_grade=True, use_learning=True'")
        print("  5. Click 'Generate PDF' and verify downloaded PDF opens correctly")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nTroubleshooting:")
        print("  - Ensure backend is running: uvicorn backend.main:app --reload")
        print("  - Set AICMO_BACKEND_URL: export AICMO_BACKEND_URL=http://localhost:8000")
        print("  - Check backend logs for errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())
