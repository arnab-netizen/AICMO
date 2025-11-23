"""
PDF export utilities for guaranteeing PDFs are always generated.

This module provides a central helper to ensure every report gets a PDF
without breaking existing code paths.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from pathlib import Path
import json


def ensure_pdf_for_report(
    report_id: str,
    markdown: str,
    meta: Optional[Dict[str, Any]] = None,
    pdf_bytes: Optional[bytes] = None,
) -> Dict[str, Any]:
    """
    Central helper to guarantee a PDF exists for a given report.

    Args:
        report_id: Unique identifier for the report
        markdown: The markdown content of the report
        meta: Optional metadata dict (title, brand_name, etc)
        pdf_bytes: Optional pre-generated PDF bytes. If not provided,
                   a simple markdown->text conversion is stored instead.

    Returns:
        Dict with pdf_path and pdf_url keys that can be added to API response.

    Usage:
        pdf_meta = ensure_pdf_for_report(
            report_id="report_12345",
            markdown=report_markdown,
            meta={"title": req.brand_name, "brand_name": req.brand_name},
        )
        # Then in API response:
        return {
            "report_id": report_id,
            "markdown": report_markdown,
            "pdf_url": pdf_meta["pdf_url"],
        }
    """
    meta = meta or {}

    # 1) Create output directory
    out_dir = Path("data/exports/pdf")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 2) Handle PDF bytes
    if pdf_bytes:
        pdf_path = out_dir / f"{report_id}.pdf"
        pdf_path.write_bytes(pdf_bytes)
    else:
        # Fallback: save markdown as text if no PDF generated yet
        # This allows graceful degradation while real PDF export is integrated
        pdf_path = out_dir / f"{report_id}.txt"
        pdf_path.write_text(markdown, encoding="utf-8")

    # 3) Build a URL that Streamlit/frontend can hit
    # Adjust route to match your actual API routing
    pdf_url = f"/api/export/pdf/{report_id}"

    return {
        "pdf_path": str(pdf_path),
        "pdf_url": pdf_url,
    }


def load_wow_presets() -> Dict[str, Any]:
    """
    Load WOW presets JSON from disk.

    Returns:
        Dict with presets config, or empty dict if file not found.
    """
    presets_path = Path("aicmo/presets/wow_presets.json")
    if presets_path.exists():
        try:
            return json.loads(presets_path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def get_preset_by_key(key: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific preset configuration by its key.

    Returns:
        Preset dict if found, None otherwise.
    """
    presets_config = load_wow_presets()
    presets_list = presets_config.get("presets", [])

    for preset in presets_list:
        if preset.get("key") == key:
            return preset

    return None
