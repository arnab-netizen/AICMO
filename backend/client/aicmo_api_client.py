"""
Thin client for /api/aicmo/generate_report endpoint.

Meant to be used by Streamlit UI and CLI tools. Provides a simple
synchronous interface to the AICMO report generation API.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from backend.main import api_aicmo_generate_report


def call_generate_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Thin client for /api/aicmo/generate_report.

    Meant to be used by Streamlit and CLI tools. Calls the FastAPI handler
    directly (in-process) rather than over HTTP for simplicity.

    Args:
        payload: Request payload dict matching GenerateRequest structure.
                 Should include:
                 - pack_key: str (e.g., "quick_social_basic")
                 - client_brief: dict with brand_name, industry, etc.
                 - Optional: stage, wow_enabled, include_agency_grade, etc.

    Returns:
        Standardized response dict:
        {
            "success": bool,
            "pack_key": str,
            "markdown": str (if success),
            "stub_used": bool,
            "quality_passed": bool,
            "error_type": str (if not success),
            "error_message": str (if not success),
            "debug_hint": str (if not success),
            ...
        }

    Example:
        >>> payload = {
        ...     "pack_key": "quick_social_basic",
        ...     "client_brief": {
        ...         "brand_name": "Acme Corp",
        ...         "industry": "Technology",
        ...         "primary_goal": "Increase brand awareness",
        ...     }
        ... }
        >>> result = call_generate_report(payload)
        >>> print(result["success"])
        True
    """
    try:
        # Call the async FastAPI handler directly
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(api_aicmo_generate_report(payload))
        finally:
            loop.close()

        # Response is already a dict from api_aicmo_generate_report
        return response

    except Exception as e:
        # Convert any unexpected exception to standardized error response
        return {
            "success": False,
            "status": "error",
            "pack_key": payload.get("pack_key", "unknown"),
            "error_type": "unexpected_error",
            "error_message": f"Client error: {type(e).__name__}: {str(e)}",
            "stub_used": False,
            "debug_hint": "Check application logs for full stack trace",
            "meta": {},
        }
