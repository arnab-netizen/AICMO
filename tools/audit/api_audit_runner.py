"""
Phase 3: Backend API Endpoint Audit
Enumerate all FastAPI endpoints and run smoke tests.
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from backend.main import app

OUT_DIR = Path(".aicmo/audit/endpoints")
OUT_DIR.mkdir(parents=True, exist_ok=True)

client = TestClient(app)

# ============================================================================
# PART 1: Enumerate all routes
# ============================================================================


def enumerate_routes():
    """List all routes in the app."""
    routes = []
    for route in app.routes:
        route_info = {
            "path": route.path,
            "methods": list(route.methods) if hasattr(route, "methods") else ["STATIC"],
            "name": route.name if hasattr(route, "name") else "unknown",
            "endpoint": str(route.endpoint) if hasattr(route, "endpoint") else "unknown",
        }
        routes.append(route_info)
    return routes


routes = enumerate_routes()
(OUT_DIR / "routes.json").write_text(json.dumps(routes, indent=2))
print(f"✓ Found {len(routes)} total routes")

# ============================================================================
# PART 2: Smoke tests for GET endpoints
# ============================================================================


def get_sample_brief():
    """Create a minimal valid ClientInputBrief for testing."""
    return {
        "brand_name": "AUDIT_TEST_BRAND",
        "industry": "technology",
        "product_service": {
            "name": "AUDIT_PRODUCT",
            "usp": "Best audit product",
            "key_features": ["feature1"],
            "value_proposition": "Great value",
        },
        "audience": {
            "type": "Directors, VP of Marketing",
            "pain_points": ["time_waste", "budget_constraints"],
        },
        "goal": "adoption",
        "assets_constraints": {
            "focus_platforms": ["LinkedIn", "Twitter"],
            "brand_adjectives": ["professional", "innovative"],
        },
    }


smoke_results = {"total_routes": len(routes), "tested": [], "skipped": [], "errored": []}

for route in routes:
    path = route["path"]
    methods = route["methods"]

    # Skip static files and openapi
    if "static" in path.lower() or "openapi" in path.lower() or path == "/":
        continue

    # Test GET endpoints with no required path params
    if "GET" in methods and "{" not in path:
        try:
            print(f"Testing GET {path}...", end=" ")
            response = client.get(path)
            result = {
                "path": path,
                "status_code": response.status_code,
                "response_length": len(response.content),
            }
            if response.status_code == 200:
                try:
                    result["response_sample"] = str(response.json())[:200]
                except:
                    result["response_type"] = response.headers.get("content-type", "unknown")
            smoke_results["tested"].append(result)
            print(f"✓ {response.status_code}")
        except Exception as e:
            smoke_results["errored"].append({"path": path, "method": "GET", "error": str(e)})
            print(f"✗ {str(e)[:50]}")

    # POST endpoints - look for test fixtures
    elif "POST" in methods:
        payload = None

        # Try common POST endpoints with known payloads
        if "/aicmo/generate" in path:
            payload = {
                "brief": get_sample_brief(),
                "persona_cards": True,
                "marketing_plan": True,
                "campaign_blueprint": True,
                "situation_analysis": True,
                "messaging_pillars": True,
                "swot_analysis": True,
                "social_calendar": True,
                "creatives": False,
                "performance_review": False,
            }
        elif "/aicmo/learn" in path:
            payload = {"content": "AUDIT_TEST_LEARN"}
        elif "/aicmo/export" in path:
            # Exports need valid reports; skip for now
            smoke_results["skipped"].append(
                {
                    "path": path,
                    "reason": "export endpoints need valid report; skipped to avoid artifacts",
                }
            )
            continue
        else:
            smoke_results["skipped"].append({"path": path, "reason": "no known sample payload"})
            continue

        if payload:
            try:
                print(f"Testing POST {path}...", end=" ")
                response = client.post(path, json=payload)
                result = {
                    "path": path,
                    "status_code": response.status_code,
                    "response_length": len(response.content),
                }
                if response.status_code == 200:
                    try:
                        resp_json = response.json()
                        result["response_keys"] = (
                            list(resp_json.keys())[:5] if isinstance(resp_json, dict) else "array"
                        )
                    except:
                        result["response_type"] = response.headers.get("content-type", "unknown")
                smoke_results["tested"].append(result)
                print(f"✓ {response.status_code}")
            except Exception as e:
                smoke_results["errored"].append(
                    {"path": path, "method": "POST", "error": str(e)[:100]}
                )
                print(f"✗ {str(e)[:50]}")

# Save smoke test results
(OUT_DIR / "smoke_test_results.json").write_text(json.dumps(smoke_results, indent=2))

print("\n" + "=" * 70)
print("SMOKE TEST SUMMARY")
print("=" * 70)
print(f"Total routes: {smoke_results['total_routes']}")
print(f"Successfully tested: {len(smoke_results['tested'])}")
print(f"Skipped (no payload): {len(smoke_results['skipped'])}")
print(f"Errored: {len(smoke_results['errored'])}")
print("=" * 70)

# Save summary
summary = f"""# Backend API Endpoint Audit

**Total Routes**: {len(routes)}
**Successfully Tested**: {len(smoke_results['tested'])}
**Skipped**: {len(smoke_results['skipped'])}
**Errored**: {len(smoke_results['errored'])}

## Test Results

All detailed results saved in:
- routes.json (full route list)
- smoke_test_results.json (test execution results)

## Tested Endpoints (200 OK)

"""

for result in smoke_results["tested"]:
    if result.get("status_code") == 200:
        summary += f"- ✅ {result['path']} ({result['status_code']})\n"

summary += "\n## Errored Endpoints\n\n"
for result in smoke_results["errored"]:
    summary += f"- ❌ {result['path']} ({result['method']}): {result['error']}\n"

summary += "\n## Skipped Endpoints\n\n"
for result in smoke_results["skipped"]:
    summary += f"- ⏭️  {result['path']}: {result['reason']}\n"

(OUT_DIR / "ENDPOINT_AUDIT_SUMMARY.md").write_text(summary)
print("\n✓ Summary written to ENDPOINT_AUDIT_SUMMARY.md")
