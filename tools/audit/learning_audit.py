"""
Phase 5 & 6: Learning Flows & Package Presets Audit
Test learn-from-report, learn-from-files, and package preset endpoints.

UPDATED (Option B+C): Using real payloads from test fixtures with request logging.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import time
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from backend.main import app

# Import real payloads from Option B
try:
    from tools.audit.real_payloads import (
        get_minimal_brief,
        get_fullstack_brief,
        get_techflow_brief,
        get_generate_request_payload,
    )
except ImportError:
    # Fallback if import path differs
    from real_payloads import (
        get_minimal_brief,
        get_generate_request_payload,
    )

OUT_DIR = Path(".aicmo/audit/memory")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Setup request logging (Option C)
captured_requests = []


def log_request_event(event_name):
    """Create event hook to capture request details."""

    def hook(request):
        if event_name == "request":
            captured_requests.append(
                {
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers),
                    "content": request.content.decode() if request.content else None,
                }
            )

    return hook


client = TestClient(app)

# ============================================================================
# PART 1: Learning from Reports
# ============================================================================

print("=" * 70)
print("PHASE 5A: Learning from Reports")
print("=" * 70)

learning_report_result = {
    "timestamp": datetime.now().isoformat(),
    "test_marker": f"AUDIT_LEARN_REPORT_{int(time.time())}",
    "steps": {"generate_report": {}, "learn_from_report": {}, "verify_in_memory": {}},
    "errors": [],
}

# Step 1: Generate a minimal report using REAL payload from test fixtures
try:
    print("Step 1: Generating report with real payload from test fixtures...", end=" ")

    # Use real minimal brief from test fixtures (Option B)
    minimal_brief = get_minimal_brief()
    payload = get_generate_request_payload(minimal_brief)

    # Log the request being sent (Option C)
    print("\n  Request payload saved for inspection")
    (OUT_DIR / "learning_generate_request.json").write_text(json.dumps(payload, indent=2))

    response = client.post("/aicmo/generate", json=payload)
    if response.status_code == 200:
        report_data = response.json()
        learning_report_result["steps"]["generate_report"]["status"] = "success"
        learning_report_result["steps"]["generate_report"]["response_keys"] = list(
            report_data.keys()
        )[:5]
        print(f"✓ ({response.status_code})")
    else:
        learning_report_result["steps"]["generate_report"]["status"] = "failed"
        learning_report_result["steps"]["generate_report"]["error"] = f"HTTP {response.status_code}"
        learning_report_result["steps"]["generate_report"]["response_text"] = response.text[:500]
        print(f"✗ ({response.status_code})")
        print(f"  Response: {response.text[:200]}")

except Exception as e:
    learning_report_result["steps"]["generate_report"]["status"] = "error"
    learning_report_result["steps"]["generate_report"]["error"] = str(e)
    learning_report_result["errors"].append(f"Generate report failed: {str(e)}")
    print(f"✗ {str(e)[:50]}")

# Step 2: Learn from report (if generation succeeded)
if learning_report_result["steps"]["generate_report"]["status"] == "success":
    try:
        print("Step 2: Calling learn-from-report endpoint...", end=" ")
        learn_payload = {"report_data": report_data, "project_id": "audit_test"}

        response = client.post("/api/learn/from-report", json=learn_payload)
        if response.status_code in [200, 201]:
            learn_response = response.json()
            learning_report_result["steps"]["learn_from_report"]["status"] = "success"
            learning_report_result["steps"]["learn_from_report"]["response"] = learn_response
            print(f"✓ ({response.status_code})")
        else:
            learning_report_result["steps"]["learn_from_report"]["status"] = "failed"
            learning_report_result["steps"]["learn_from_report"][
                "error"
            ] = f"HTTP {response.status_code}: {response.text[:100]}"
            print(f"✗ ({response.status_code})")

    except Exception as e:
        learning_report_result["steps"]["learn_from_report"]["status"] = "error"
        learning_report_result["steps"]["learn_from_report"]["error"] = str(e)
        learning_report_result["errors"].append(f"Learn endpoint failed: {str(e)}")
        print(f"✗ {str(e)[:50]}")

# Step 3: Verify in memory
try:
    print("Step 3: Verifying in memory...", end=" ")
    from aicmo.memory.engine import retrieve_relevant_blocks

    results = retrieve_relevant_blocks(learning_report_result["test_marker"], limit=5)

    if results and len(results) > 0:
        learning_report_result["steps"]["verify_in_memory"]["status"] = "success"
        learning_report_result["steps"]["verify_in_memory"]["results_count"] = len(results)
        print(f"✓ ({len(results)} results)")
    else:
        learning_report_result["steps"]["verify_in_memory"]["status"] = "not_found"
        learning_report_result["steps"]["verify_in_memory"]["results_count"] = 0
        learning_report_result["errors"].append("Test marker not found in memory after learning")
        print("⚠ (not found in memory)")

except Exception as e:
    learning_report_result["steps"]["verify_in_memory"]["status"] = "error"
    learning_report_result["steps"]["verify_in_memory"]["error"] = str(e)
    learning_report_result["errors"].append(f"Memory verification failed: {str(e)}")
    print(f"✗ {str(e)[:50]}")

(OUT_DIR / "learning_from_report_result.json").write_text(
    json.dumps(learning_report_result, indent=2)
)

# ============================================================================
# PART 2: Learning from Training Files
# ============================================================================

print("\n" + "=" * 70)
print("PHASE 5B: Learning from Training Files")
print("=" * 70)

learning_files_result = {
    "timestamp": datetime.now().isoformat(),
    "test_marker": f"AUDIT_TRAINING_FILE_{int(time.time())}",
    "file_created": None,
    "file_size": None,
    "upload_status": "not_attempted",
    "learn_status": "not_attempted",
    "memory_verified": False,
    "errors": [],
}

# Step 1: Create temporary test file
try:
    print("Step 1: Creating temporary training file...", end=" ")
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write(f"Training file audit marker: {learning_files_result['test_marker']}\n")
        f.write("This is a test training file for the audit.\n")
        f.write("It contains content that should be learned by the memory engine.\n")
        temp_file_path = f.name

    learning_files_result["file_created"] = temp_file_path
    learning_files_result["file_size"] = Path(temp_file_path).stat().st_size
    print(f"✓ ({learning_files_result['file_size']} bytes)")

except Exception as e:
    learning_files_result["errors"].append(f"File creation failed: {str(e)}")
    print(f"✗ {str(e)[:50]}")
    temp_file_path = None

# Step 2: Upload/learn from file (if file created)
if temp_file_path:
    try:
        print("Step 2: Uploading file to learn endpoint...", end=" ")
        with open(temp_file_path, "rb") as f:
            files = {"file": (Path(temp_file_path).name, f, "text/plain")}
            response = client.post("/api/learn/from-files", files=files)

        if response.status_code in [200, 201]:
            learn_response = response.json()
            learning_files_result["learn_status"] = "success"
            learning_files_result["response"] = learn_response
            print(f"✓ ({response.status_code})")
        else:
            learning_files_result["learn_status"] = "failed"
            learning_files_result["response_error"] = (
                f"HTTP {response.status_code}: {response.text[:100]}"
            )
            print(f"✗ ({response.status_code})")

    except Exception as e:
        learning_files_result["learn_status"] = "error"
        learning_files_result["error"] = str(e)
        learning_files_result["errors"].append(f"File upload failed: {str(e)}")
        print(f"✗ {str(e)[:50]}")

    # Step 3: Verify in memory
    if learning_files_result["learn_status"] == "success":
        try:
            print("Step 3: Verifying in memory...", end=" ")
            from aicmo.memory.engine import retrieve_relevant_blocks

            results = retrieve_relevant_blocks(learning_files_result["test_marker"], limit=5)

            if results and len(results) > 0:
                learning_files_result["memory_verified"] = True
                print(f"✓ ({len(results)} results)")
            else:
                learning_files_result["memory_verified"] = False
                learning_files_result["errors"].append(
                    "Test marker not found in memory after file learning"
                )
                print("⚠ (not found in memory)")

        except Exception as e:
            learning_files_result["errors"].append(f"Memory verification failed: {str(e)}")
            print(f"✗ {str(e)[:50]}")

    # Cleanup
    try:
        Path(temp_file_path).unlink()
    except:
        pass

(OUT_DIR / "learning_from_files_result.json").write_text(
    json.dumps(learning_files_result, indent=2)
)

# ============================================================================
# PART 3: Package Presets
# ============================================================================

print("\n" + "=" * 70)
print("PHASE 6: Package Presets / Fiverr Bundles")
print("=" * 70)

# First, find PACKAGE_PRESETS
try:
    from streamlit_pages.aicmo_operator import PACKAGE_PRESETS

    print(f"✓ Found {len(PACKAGE_PRESETS)} presets")
except ImportError:
    PACKAGE_PRESETS = {}
    print("⚠ Could not import PACKAGE_PRESETS from streamlit_pages.aicmo_operator")

preset_audit_results = {
    "timestamp": datetime.now().isoformat(),
    "total_presets": len(PACKAGE_PRESETS),
    "presets_tested": [],
    "errors": [],
}

# Test a few presets
test_preset_names = list(PACKAGE_PRESETS.keys())[:2] if PACKAGE_PRESETS else []

for preset_name in test_preset_names:
    try:
        print(f"Testing preset: {preset_name}...", end=" ")
        preset = PACKAGE_PRESETS[preset_name]

        # Use real brief from test fixtures (Option B)
        minimal_brief = get_minimal_brief()

        payload = {
            "brief": minimal_brief.model_dump(),
            # Apply preset flags
            "persona_cards": preset.get("persona_cards", False),
            "marketing_plan": preset.get("marketing_plan", False),
            "campaign_blueprint": preset.get("campaign_blueprint", False),
            "situation_analysis": preset.get("situation_analysis", False),
            "messaging_pillars": preset.get("messaging_pillars", False),
            "swot_analysis": preset.get("swot_analysis", False),
            "social_calendar": preset.get("social_calendar", False),
            "creatives": preset.get("creatives", False),
            "performance_review": preset.get("performance_review", False),
        }

        response = client.post("/aicmo/generate", json=payload)

        if response.status_code == 200:
            report_data = response.json()
            preset_result = {
                "name": preset_name,
                "status": "success",
                "status_code": response.status_code,
                "preset_flags": preset,
                "response_keys": list(report_data.keys()),
                "sections_present": [
                    k for k in report_data.keys() if report_data.get(k) is not None
                ],
            }
            preset_audit_results["presets_tested"].append(preset_result)
            print("✓")
        else:
            preset_result = {
                "name": preset_name,
                "status": "failed",
                "status_code": response.status_code,
                "error": response.text[:100],
            }
            preset_audit_results["presets_tested"].append(preset_result)
            print(f"✗ ({response.status_code})")

    except Exception as e:
        preset_audit_results["errors"].append(f"{preset_name}: {str(e)}")
        print(f"✗ {str(e)[:50]}")

(OUT_DIR / "package_preset_audit_result.json").write_text(
    json.dumps(preset_audit_results, indent=2)
)

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "=" * 70)
print("PHASES 5 & 6 AUDIT SUMMARY")
print("=" * 70)
print(
    f"Learning from Reports: {learning_report_result['steps']['learn_from_report'].get('status', 'N/A')}"
)
print(f"Learning from Files: {learning_files_result['learn_status']}")
print(f"Package Presets Tested: {len(preset_audit_results['presets_tested'])}")
print("=" * 70)
print("\nDetails saved to:")
print("  - learning_from_report_result.json")
print("  - learning_from_files_result.json")
print("  - package_preset_audit_result.json")
