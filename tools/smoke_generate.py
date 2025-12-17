#!/usr/bin/env python3
"""
Smoke test for Streamlit ↔ Backend integration.

Tests:
1. Backend URL configuration
2. Generate endpoint availability
3. Deliverable contract compliance
4. Provider configuration
5. Error handling

Usage: python tools/smoke_generate.py

Exit codes:
  0 = All tests passed
  1 = Configuration error
  2 = Endpoint error
  3 = Contract validation error
  4 = Unexpected error
"""

import os
import sys
import json
import uuid
import logging
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
log = logging.getLogger("smoke_test")


def main():
    """Run smoke tests"""
    
    # Test 1: Backend URL configuration
    log.info("=" * 80)
    log.info("TEST 1: Backend URL Configuration")
    log.info("=" * 80)
    
    backend_url = os.getenv("BACKEND_URL") or os.getenv("AICMO_BACKEND_URL")
    if not backend_url:
        log.error("❌ FAILED: BACKEND_URL or AICMO_BACKEND_URL not set")
        log.info("Set environment variable:")
        log.info("  export BACKEND_URL=http://localhost:8000")
        return 1
    
    backend_url = backend_url.rstrip("/")
    log.info(f"✅ Backend URL configured: {backend_url}")
    
    # Test 2: Check env vars (names only, no values)
    log.info("")
    log.info("=" * 80)
    log.info("TEST 2: Provider Configuration (names only)")
    log.info("=" * 80)
    
    provider_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GROQ_API_KEY",
        "MISTRAL_API_KEY",
    ]
    
    configured = []
    for var in provider_vars:
        if os.getenv(var):
            configured.append(var)
            log.info(f"  ✅ {var} configured")
        else:
            log.info(f"  ❌ {var} not set")
    
    if not configured:
        log.warning("⚠️  No LLM providers configured, will use stubs")
    else:
        log.info(f"✅ {len(configured)} provider(s) available")
    
    # Test 3: Test endpoint
    log.info("")
    log.info("=" * 80)
    log.info("TEST 3: Endpoint Availability")
    log.info("=" * 80)
    
    try:
        import requests
    except ImportError:
        log.error("❌ requests library not installed")
        return 4
    
    endpoint = "/api/v1/campaigns/generate"
    test_payload = {
        "campaign_name": "SMOKE_TEST",
        "objectives": ["Awareness", "Engagement"],
        "platforms": ["LinkedIn"],
        "budget": 5000,
        "timeline_days": 30,
    }
    
    trace_id = str(uuid.uuid4())
    headers = {
        "Content-Type": "application/json",
        "X-Trace-ID": trace_id,
    }
    
    log.info(f"POST {backend_url}{endpoint}")
    log.info(f"Trace ID: {trace_id}")
    
    try:
        response = requests.post(
            f"{backend_url}{endpoint}",
            json=test_payload,
            headers=headers,
            timeout=30,
        )
        log.info(f"Status: {response.status_code}")
        
    except requests.ConnectionError:
        log.error(f"❌ FAILED: Cannot connect to {backend_url}")
        log.info("Is the backend running? Try:")
        log.info(f"  python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000")
        return 2
    
    except requests.Timeout:
        log.error(f"❌ FAILED: Request timed out after 30s")
        return 2
    
    except Exception as e:
        log.error(f"❌ FAILED: {type(e).__name__}: {e}")
        return 4
    
    if response.status_code != 200:
        log.error(f"❌ FAILED: Expected 200, got {response.status_code}")
        log.info(f"Response: {response.text[:200]}")
        return 2
    
    log.info("✅ Endpoint responded with 200")
    
    # Test 4: Validate response envelope
    log.info("")
    log.info("=" * 80)
    log.info("TEST 4: Response Envelope Validation")
    log.info("=" * 80)
    
    try:
        data = response.json()
    except json.JSONDecodeError:
        log.error("❌ FAILED: Response is not valid JSON")
        return 3
    
    log.info(f"Status: {data.get('status')}")
    log.info(f"Run ID: {data.get('run_id')}")
    log.info(f"Module: {data.get('module')}")
    
    # Check required fields
    errors = []
    
    if "status" not in data:
        errors.append("Missing 'status' field")
    elif data["status"] not in ["SUCCESS", "FAILED", "PARTIAL"]:
        errors.append(f"Invalid status: {data['status']}")
    
    if "run_id" not in data:
        errors.append("Missing 'run_id' field")
    
    if "module" not in data:
        errors.append("Missing 'module' field")
    
    if "meta" not in data:
        errors.append("Missing 'meta' field")
    elif not isinstance(data["meta"], dict):
        errors.append("'meta' must be dict")
    else:
        if "timestamp" not in data["meta"]:
            errors.append("meta missing 'timestamp'")
        if "provider" not in data["meta"]:
            errors.append("meta missing 'provider'")
    
    if "deliverables" not in data:
        errors.append("Missing 'deliverables' field")
    elif not isinstance(data["deliverables"], list):
        errors.append("'deliverables' must be list")
    else:
        # SUCCESS requires deliverables
        if data.get("status") == "SUCCESS" and len(data["deliverables"]) == 0:
            errors.append("SUCCESS status requires non-empty deliverables")
        
        # Check each deliverable
        for i, d in enumerate(data.get("deliverables", [])):
            if "id" not in d:
                errors.append(f"deliverables[{i}] missing 'id'")
            if "kind" not in d:
                errors.append(f"deliverables[{i}] missing 'kind'")
            if "title" not in d:
                errors.append(f"deliverables[{i}] missing 'title'")
            if "content_markdown" not in d:
                errors.append(f"deliverables[{i}] missing 'content_markdown'")
            elif not str(d.get("content_markdown", "")).strip():
                errors.append(f"deliverables[{i}] content_markdown is empty")
    
    if errors:
        log.error("❌ FAILED: Contract validation errors:")
        for err in errors:
            log.error(f"  - {err}")
        return 3
    
    # Test 5: Print results
    log.info("")
    log.info("=" * 80)
    log.info("TEST 5: Response Summary")
    log.info("=" * 80)
    
    log.info(f"Status: {data.get('status')}")
    log.info(f"Run ID: {data.get('run_id')}")
    log.info(f"Provider: {data.get('meta', {}).get('provider', 'unknown')}")
    log.info(f"Model: {data.get('meta', {}).get('model', 'unknown')}")
    log.info(f"Deliverables: {len(data.get('deliverables', []))}")
    
    for i, d in enumerate(data.get("deliverables", [])):
        log.info(f"  [{i}] {d.get('kind')} | {d.get('title', 'untitled')}")
        content_len = len(d.get("content_markdown", ""))
        log.info(f"       Content: {content_len} chars")
    
    # Final result
    log.info("")
    log.info("=" * 80)
    log.info("✅ ALL TESTS PASSED")
    log.info("=" * 80)
    log.info("")
    log.info("Integration is working correctly:")
    log.info("  ✅ Backend URL configured")
    log.info("  ✅ Endpoint responsive")
    log.info("  ✅ Response matches contract")
    log.info("  ✅ Deliverables present with content")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
