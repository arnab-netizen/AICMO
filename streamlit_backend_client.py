"""
Streamlit → Backend HTTP client with safe instrumentation.

All Streamlit generate operations use this client.
Rules:
- No secrets printed
- Trace ID for correlation
- Safe error handling
- Returns deliverables envelope
"""

import os
import json
import logging
import requests
import uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass

log = logging.getLogger("streamlit_backend_client")


@dataclass
class BackendResponse:
    """Parsed backend response"""
    success: bool
    status: str
    run_id: str
    deliverables: list
    meta: dict
    error: Optional[dict] = None
    trace_id: Optional[str] = None
    raw_text: Optional[str] = None


def get_backend_url() -> Optional[str]:
    """
    Get backend URL from environment.
    
    Returns:
        Backend URL or None if not configured
    """
    url = os.getenv("BACKEND_URL") or os.getenv("AICMO_BACKEND_URL")
    return url.rstrip("/") if url else None


def backend_post_json(
    path: str,
    payload: Dict[str, Any],
    timeout_s: int = 120,
) -> BackendResponse:
    """
    POST JSON to backend and return parsed response.
    
    Args:
        path: Endpoint path (e.g., "/api/v1/campaigns/generate")
        payload: Request payload dict
        timeout_s: Request timeout in seconds
        
    Returns:
        BackendResponse with status, deliverables, error
        
    Safety:
        - Never logs payload or secrets
        - Generates trace_id for correlation
        - Returns envelope with explicit error on failure
    """
    backend_url = get_backend_url()
    if not backend_url:
        return BackendResponse(
            success=False,
            status="FAILED",
            run_id="unknown",
            deliverables=[],
            meta={},
            error={
                "type": "CONFIGURATION_ERROR",
                "message": "BACKEND_URL or AICMO_BACKEND_URL not configured. Set env var and restart Streamlit.",
                "code": 503,
            },
            trace_id=None,
        )
    
    # Generate trace ID for this request
    trace_id = str(uuid.uuid4())
    
    # Log request initiation (safe: no payload, no secrets)
    log.info(f"HTTP_REQUEST path={path} trace_id={trace_id}")
    
    try:
        url = f"{backend_url}{path}"
        headers = {
            "Content-Type": "application/json",
            "X-Trace-ID": trace_id,
        }
        
        # Make request
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=timeout_s,
        )
        
        # Log response status (safe: just status code and trace)
        log.info(f"HTTP_RESPONSE status={response.status_code} trace_id={trace_id}")
        
        # Parse response
        if response.status_code == 200:
            try:
                data = response.json()
                return BackendResponse(
                    success=data.get("status") == "SUCCESS",
                    status=data.get("status", "UNKNOWN"),
                    run_id=data.get("run_id", "unknown"),
                    deliverables=data.get("deliverables", []),
                    meta=data.get("meta", {}),
                    error=data.get("error"),
                    trace_id=trace_id,
                    raw_text=response.text,
                )
            except json.JSONDecodeError as e:
                log.error(f"JSON_DECODE_ERROR trace_id={trace_id} error_type={type(e).__name__}")
                return BackendResponse(
                    success=False,
                    status="FAILED",
                    run_id="unknown",
                    deliverables=[],
                    meta={},
                    error={
                        "type": "RESPONSE_PARSE_ERROR",
                        "message": "Backend returned invalid JSON",
                        "code": 200,
                    },
                    trace_id=trace_id,
                )
        else:
            log.warning(f"HTTP_ERROR status={response.status_code} trace_id={trace_id}")
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:500]}
            
            return BackendResponse(
                success=False,
                status="FAILED",
                run_id="unknown",
                deliverables=[],
                meta={},
                error={
                    "type": f"HTTP_{response.status_code}",
                    "message": error_data.get("message") or error_data.get("detail") or "Unknown error",
                    "code": response.status_code,
                },
                trace_id=trace_id,
            )
    
    except requests.Timeout:
        log.error(f"TIMEOUT trace_id={trace_id} timeout_s={timeout_s}")
        return BackendResponse(
            success=False,
            status="FAILED",
            run_id="unknown",
            deliverables=[],
            meta={},
            error={
                "type": "TIMEOUT",
                "message": f"Backend request timed out after {timeout_s}s",
                "code": 504,
            },
            trace_id=trace_id,
        )
    
    except requests.ConnectionError as e:
        log.error(f"CONNECTION_ERROR trace_id={trace_id} backend_url={backend_url}")
        return BackendResponse(
            success=False,
            status="FAILED",
            run_id="unknown",
            deliverables=[],
            meta={},
            error={
                "type": "CONNECTION_ERROR",
                "message": f"Cannot connect to backend at {backend_url}",
                "code": 503,
            },
            trace_id=trace_id,
        )
    
    except Exception as e:
        log.error(f"UNEXPECTED_ERROR trace_id={trace_id} error_type={type(e).__name__}")
        return BackendResponse(
            success=False,
            status="FAILED",
            run_id="unknown",
            deliverables=[],
            meta={},
            error={
                "type": "INTERNAL_ERROR",
                "message": "Unexpected error communicating with backend",
                "code": 500,
            },
            trace_id=trace_id,
        )


def validate_response(resp: BackendResponse) -> tuple[bool, Optional[str]]:
    """
    Validate response matches deliverable contract.
    
    Args:
        resp: BackendResponse to validate
        
    Returns:
        (is_valid, error_message)
    """
    if not resp.status or resp.status not in ["SUCCESS", "FAILED", "PARTIAL"]:
        return False, f"Invalid status: {resp.status}"
    
    if not resp.run_id:
        return False, "Missing run_id"
    
    if not isinstance(resp.meta, dict):
        return False, "meta must be dict"
    
    if "timestamp" not in resp.meta:
        return False, "meta missing timestamp"
    
    if "provider" not in resp.meta:
        return False, "meta missing provider"
    
    if not isinstance(resp.deliverables, list):
        return False, "deliverables must be list"
    
    # SUCCESS requires non-empty deliverables
    if resp.status == "SUCCESS" and len(resp.deliverables) == 0:
        return False, "SUCCESS status requires at least one deliverable"
    
    # Check each deliverable
    for i, d in enumerate(resp.deliverables):
        if not isinstance(d, dict):
            return False, f"deliverables[{i}] must be dict"
        
        if "id" not in d:
            return False, f"deliverables[{i}] missing id"
        
        if "kind" not in d:
            return False, f"deliverables[{i}] missing kind"
        
        if "title" not in d:
            return False, f"deliverables[{i}] missing title"
        
        if "content_markdown" not in d:
            return False, f"deliverables[{i}] missing content_markdown"
        
        content = d.get("content_markdown")
        if isinstance(content, str) and not content.strip():
            return False, f"deliverables[{i}] content_markdown cannot be empty"
    
    return True, None
