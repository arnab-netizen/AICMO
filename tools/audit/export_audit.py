"""
Phase 6 (continued): Export Flows Audit
Test PDF, PPTX, and ZIP export endpoints.

UPDATED (Option B+C): Using real payloads from test fixtures with request logging.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from backend.main import app

# Import real payloads from Option B
try:
    from tools.audit.real_payloads import (
        get_minimal_brief,
        get_generate_request_payload,
    )
except ImportError:
    # Fallback if import path differs
    from real_payloads import (
        get_minimal_brief,
        get_generate_request_payload,
    )

OUT_DIR = Path(".aicmo/audit/endpoints")
OUT_DIR.mkdir(parents=True, exist_ok=True)

client = TestClient(app)

print("=" * 70)
print("PHASE 6: Export Flows Audit (UPDATED with Real Payloads)")
print("=" * 70)

export_results = {
    "timestamp": datetime.now().isoformat(),
    "exports_tested": [],
    "errors": [],
    "note": "Using real payloads from backend test fixtures (Option B)",
}

# First generate a real report using test fixture payload (Option B)
print("\nGenerating sample report with real payload from test fixtures...")
generated_report = None
try:
    minimal_brief = get_minimal_brief()
    payload = get_generate_request_payload(minimal_brief)

    # Save request for inspection (Option C)
    (OUT_DIR / "export_generate_request.json").write_text(json.dumps(payload, indent=2))

    response = client.post("/aicmo/generate", json=payload)
    if response.status_code != 200:
        print(f"⚠️  Generate failed: {response.status_code}")
        print(f"  Response: {response.text[:300]}")
        export_results["errors"].append(f"Generate failed: {response.status_code}")
    else:
        generated_report = response.json()
        print("✓ Report generated successfully")

        # Save the generated report for export testing
        (OUT_DIR / "export_sample_report.json").write_text(
            json.dumps(generated_report, indent=2, default=str)
        )

except Exception as e:
    print(f"✗ Error generating report: {e}")
    export_results["errors"].append(f"Report generation error: {str(e)}")

# Test PDF export with simple markdown
print("\nTesting PDF export...", end=" ")
try:
    payload = {
        "markdown": "# AICMO Audit Export Test\n\nThis is a test PDF export from the audit suite.\n\nMarketing Plan: Test summary"
    }
    response = client.post("/aicmo/export/pdf", json=payload)

    if response.status_code == 200:
        export_results["exports_tested"].append(
            {
                "type": "PDF",
                "status": "success",
                "status_code": response.status_code,
                "content_length": len(response.content),
                "content_type": response.headers.get("content-type"),
            }
        )

        # Save sample PDF
        pdf_path = OUT_DIR / "audit_export.pdf"
        pdf_path.write_bytes(response.content)
        print(f"✓ ({len(response.content)} bytes)")
    else:
        error_body = response.text[:200] if response.text else "No error body"
        export_results["exports_tested"].append(
            {
                "type": "PDF",
                "status": "failed",
                "status_code": response.status_code,
                "error": error_body,
            }
        )
        print(f"✗ ({response.status_code})")

except Exception as e:
    export_results["exports_tested"].append({"type": "PDF", "status": "error", "error": str(e)})
    export_results["errors"].append(f"PDF export error: {str(e)}")
    print(f"✗ {str(e)[:50]}")

# If we have a generated report, test export with real data
if generated_report:
    print("\nTesting PPTX export with generated report...", end=" ")
    try:
        minimal_brief = get_minimal_brief()
        payload = {"brief": minimal_brief.model_dump(), "output": generated_report}

        # Save request for inspection (Option C)
        (OUT_DIR / "export_pptx_request.json").write_text(
            json.dumps(payload, indent=2, default=str)[:1000]
        )

        response = client.post("/aicmo/export/pptx", json=payload)

        if response.status_code == 200:
            export_results["exports_tested"].append(
                {
                    "type": "PPTX",
                    "status": "success",
                    "status_code": response.status_code,
                    "content_length": len(response.content),
                    "content_type": response.headers.get("content-type"),
                }
            )

            # Save sample PPTX
            pptx_path = OUT_DIR / "audit_export.pptx"
            pptx_path.write_bytes(response.content)
            print(f"✓ ({len(response.content)} bytes)")
        else:
            error_body = response.text[:300] if response.text else "No error body"
            export_results["exports_tested"].append(
                {
                    "type": "PPTX",
                    "status": "failed",
                    "status_code": response.status_code,
                    "error": error_body,
                }
            )
            print(f"✗ ({response.status_code})")
            print(f"  Error: {error_body}")

    except Exception as e:
        export_results["exports_tested"].append(
            {"type": "PPTX", "status": "error", "error": str(e)}
        )
        export_results["errors"].append(f"PPTX export error: {str(e)}")
        print(f"✗ {str(e)[:50]}")

    # Test ZIP export
    print("\nTesting ZIP export with generated report...", end=" ")
    try:
        minimal_brief = get_minimal_brief()
        payload = {"brief": minimal_brief.model_dump(), "output": generated_report}

        response = client.post("/aicmo/export/zip", json=payload)

        if response.status_code == 200:
            export_results["exports_tested"].append(
                {
                    "type": "ZIP",
                    "status": "success",
                    "status_code": response.status_code,
                    "content_length": len(response.content),
                    "content_type": response.headers.get("content-type"),
                }
            )

            # Save sample ZIP
            zip_path = OUT_DIR / "audit_export.zip"
            zip_path.write_bytes(response.content)
            print(f"✓ ({len(response.content)} bytes)")
        else:
            error_body = response.text[:300] if response.text else "No error body"
            export_results["exports_tested"].append(
                {
                    "type": "ZIP",
                    "status": "failed",
                    "status_code": response.status_code,
                    "error": error_body,
                }
            )
            print(f"✗ ({response.status_code})")
            print(f"  Error: {error_body}")

    except Exception as e:
        export_results["exports_tested"].append({"type": "ZIP", "status": "error", "error": str(e)})
        export_results["errors"].append(f"ZIP export error: {str(e)}")
        print(f"✗ {str(e)[:50]}")

# Save results
(OUT_DIR / "export_test_results.json").write_text(json.dumps(export_results, indent=2))

print("\n" + "=" * 70)
print("EXPORT FLOWS SUMMARY")
print("=" * 70)
print("Note: Using REAL payloads from test fixtures (Option B)")
print()
for result in export_results["exports_tested"]:
    status_icon = (
        "✅" if result["status"] == "success" else "⚠️ " if result["status"] == "failed" else "❌"
    )
    print(
        f"{status_icon} {result['type']:6s}: {result['status']:8s} (HTTP {result.get('status_code', 'N/A')})"
    )

if export_results["errors"]:
    print("\nErrors:")
    for error in export_results["errors"]:
        print(f"  - {error}")

print("\n" + "=" * 70)
print("Results saved to export_test_results.json")
print("Request logs saved to export_*_request.json (Option C)")
