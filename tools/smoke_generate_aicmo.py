#!/usr/bin/env python3
"""
COMPREHENSIVE Smoke Test: AICMO /aicmo/generate Endpoint

Tests that the backend:
1. Returns HTTP 200 for all use_cases (intake, strategy, creatives, campaigns, etc.)
2. Returns status=SUCCESS (or properly formatted FAILED)
3. Returns non-empty deliverables[] with content_markdown for each
4. Returns proper meta (provider, model, trace_id, run_id)
5. Each deliverable has: id, kind, title, content_markdown (no empty strings)

Requirements:
- Backend running on BACKEND_URL (default: http://localhost:8000)
- AICMO_DEV_STUBS can be "0" (test real LLM) or "1" (test stub mode)

Usage:
    python tools/smoke_generate_aicmo.py
    
    # Test with stubs
    AICMO_DEV_STUBS=1 python tools/smoke_generate_aicmo.py
    
    # Test with real LLM (requires API keys)
    AICMO_USE_LLM=1 python tools/smoke_generate_aicmo.py
"""

import os
import sys
import json
import uuid
import requests
from datetime import datetime
from typing import Dict, Any, Tuple

BACKEND_URL = os.getenv("BACKEND_URL") or os.getenv("AICMO_BACKEND_URL") or "http://localhost:8000"
DEV_STUBS = os.getenv("AICMO_DEV_STUBS", "0")
USE_LLM = os.getenv("AICMO_USE_LLM", "0")

def test_use_case(use_case: str, payload_override: Dict[str, Any] = None) -> Tuple[bool, str, int]:
    """
    Test a single use_case.
    
    Returns: (success: bool, message: str, content_length: int)
    """
    try:
        url = f"{BACKEND_URL}/aicmo/generate"
        
        # Build payload based on use_case
        if payload_override:
            payload = payload_override
        else:
            payload = {
                "use_case": use_case,
                "brief": f"Test {use_case} generation",
                "client_email": "test@example.com",
                "metadata": {}
            }
            
            # Add use_case-specific fields
            if use_case == "intake":
                payload["metadata"] = {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "company": "Test Corp"
                }
            elif use_case in ["execution", "monitoring", "delivery"]:
                payload["campaign_id"] = f"test_campaign_{use_case}"
            elif use_case == "delivery":
                payload["report_type"] = "Final"
        
        headers = {
            "X-Trace-ID": str(uuid.uuid4()),
            "Content-Type": "application/json"
        }
        
        # POST request
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        # Check HTTP status
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}: {response.text[:100]}", 0
        
        # Parse JSON response
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON response: {str(e)}", 0
        
        # Check status field
        status = data.get("status", "UNKNOWN")
        if status not in ["SUCCESS", "FAILED", "PARTIAL"]:
            return False, f"Invalid status '{status}'", 0
        
        # FAILED is OK if properly formatted, but we'll report it
        if status == "FAILED":
            error = data.get("error", {})
            if isinstance(error, dict):
                msg = error.get("message", "Unknown error")
            else:
                msg = str(error)[:100]
            return False, f"FAILED: {msg}", 0
        
        # SUCCESS path: check deliverables
        deliverables = data.get("deliverables", [])
        if not isinstance(deliverables, list):
            return False, f"deliverables not a list (got {type(deliverables).__name__})", 0
        
        if len(deliverables) == 0:
            return False, f"deliverables[] is EMPTY (CRITICAL: must have content)", 0
        
        # Validate each deliverable
        total_content_length = 0
        for idx, deliv in enumerate(deliverables):
            if not isinstance(deliv, dict):
                return False, f"deliverable[{idx}] not a dict", 0
            
            # CRITICAL: content_markdown must exist and be non-empty
            content_md = deliv.get("content_markdown", "")
            if not isinstance(content_md, str):
                return False, f"deliverable[{idx}].content_markdown not a string (got {type(content_md).__name__})", 0
            
            content_md_stripped = content_md.strip()
            if not content_md_stripped:
                return False, f"deliverable[{idx}].content_markdown is EMPTY", 0
            
            if len(content_md_stripped) < 10:
                return False, f"deliverable[{idx}].content_markdown too short ({len(content_md_stripped)} chars)", 0
            
            total_content_length += len(content_md_stripped)
            
            # Check title
            title = deliv.get("title")
            if not title or not isinstance(title, str) or not title.strip():
                return False, f"deliverable[{idx}].title missing/invalid", 0
            
            # Check kind
            kind = deliv.get("kind")
            if not kind or not isinstance(kind, str) or not kind.strip():
                return False, f"deliverable[{idx}].kind missing/invalid", 0
            
            # Check id
            deliv_id = deliv.get("id")
            if not deliv_id or not isinstance(deliv_id, str):
                return False, f"deliverable[{idx}].id missing/invalid", 0
        
        # Check meta
        meta = data.get("meta", {})
        provider = meta.get("provider")
        model = meta.get("model")
        
        if not provider or not isinstance(provider, str) or not provider.strip():
            return False, f"meta.provider missing/invalid: {provider}", 0
        
        if not model or not isinstance(model, str) or not model.strip():
            return False, f"meta.model missing/invalid: {model}", 0
        
        # Check run_id
        run_id = data.get("run_id")
        if not run_id:
            return False, f"run_id missing", 0
        
        # Success!
        message = f"✓ {len(deliverables)} deliverable(s), {total_content_length} chars, provider={provider}"
        return True, message, total_content_length
    
    except requests.exceptions.ConnectionError:
        return False, f"Connection refused (backend not at {BACKEND_URL})", 0
    except requests.exceptions.Timeout:
        return False, f"Request timeout (30s)", 0
    except Exception as e:
        return False, f"Error: {str(e)[:80]}", 0


def main():
    print("=" * 80)
    print("AICMO /aicmo/generate COMPREHENSIVE SMOKE TEST")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Dev Stubs Enabled: {DEV_STUBS}")
    print(f"Use LLM: {USE_LLM}")
    print()
    
    # Test cases for all major use_cases
    test_cases = [
        ("intake", None),
        ("strategy", None),
        ("creatives", None),
        ("execution", None),
        ("monitoring", None),
        ("delivery", None),
    ]
    
    results = {}
    passed = 0
    failed = 0
    total_content = 0
    
    for use_case, payload_override in test_cases:
        print(f"[{use_case.upper():12}] Testing...", end=" ", flush=True)
        success, message, content_len = test_use_case(use_case, payload_override)
        results[use_case] = {
            "success": success,
            "message": message,
            "content_length": content_len
        }
        
        if success:
            print(f"✅ PASS  {message}")
            passed += 1
            total_content += content_len
        else:
            print(f"❌ FAIL  {message}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)
    
    if failed > 0:
        print("\n❌ FAILED TEST CASES:")
        for use_case, result in results.items():
            if not result["success"]:
                print(f"  - {use_case}: {result['message']}")
        print()
        return 1
    else:
        print("\n✅ ALL TESTS PASSED")
        print(f"\nTotal deliverable content generated: {total_content} characters")
        print("\nEvidence of real content generation:")
        for use_case, result in results.items():
            print(f"  {use_case:15} {result['message']}")
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())

