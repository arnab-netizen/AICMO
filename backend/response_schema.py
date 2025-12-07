"""
Standardized response schema for AICMO API endpoints.

Ensures consistent error handling and response structure across all packs.
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional


ErrorType = Literal[
    "quality_gate_failed",
    "blank_pdf",
    "llm_unavailable",
    "llm_failure",  # LLM exists but failed during generation
    "llm_chain_failed",  # Both OpenAI and Perplexity failed
    "stub_in_production_forbidden",  # Stub was generated when production LLM keys exist
    "validation_error",
    "unexpected_error",
    "runtime_quality_failed",
    "pdf_render_error",
    "agency_pipeline_error",
    "empty_report",
]


def success_response(
    pack_key: str,
    markdown: str,
    stub_used: bool = False,
    quality_passed: bool = True,
    pdf_bytes_b64: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
    brand_strategy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build standardized success response.

    Args:
        pack_key: Pack identifier (e.g., "quick_social_basic")
        markdown: Generated markdown report content
        stub_used: Whether stub content was used instead of LLM
        quality_passed: Whether quality checks passed
        pdf_bytes_b64: Optional base64-encoded PDF bytes
        meta: Optional metadata (domain, brief hash, etc.)

    Returns:
        Standardized success response dict
    """
    response = {
        "success": True,
        "status": "success",  # Legacy compatibility
        "pack_key": pack_key,
        "stub_used": stub_used,
        "quality_passed": quality_passed,
        "report_markdown": markdown,  # Legacy key name
        "markdown": markdown,
    }

    if pdf_bytes_b64:
        response["pdf_bytes_b64"] = pdf_bytes_b64

    if meta:
        response["meta"] = meta

    if brand_strategy is not None:
        response["brand_strategy"] = brand_strategy

    return response


def error_response(
    pack_key: str,
    error_type: ErrorType,
    error_message: str,
    stub_used: bool = False,
    debug_hint: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build standardized error response.

    Args:
        pack_key: Pack identifier
        error_type: Specific error category
        error_message: Client-safe error description
        stub_used: Whether stub was attempted
        debug_hint: Internal debugging information (no secrets)
        meta: Optional metadata

    Returns:
        Standardized error response dict
    """
    response = {
        "success": False,
        "status": "error",  # Legacy compatibility
        "pack_key": pack_key,
        "stub_used": stub_used,
        "error_type": error_type,
        "error": error_type,
        "error_message": error_message,
        "detail": error_message,
        "report_markdown": None,
        "markdown": None,
    }

    if debug_hint:
        response["debug_hint"] = debug_hint

    if meta:
        response["meta"] = meta

    return response
