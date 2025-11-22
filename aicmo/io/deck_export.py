"""Agency-grade deck export (PDF/PPTX)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Sequence, Tuple


@dataclass
class DeckArtifacts:
    """Container for PDF and PPTX deck bytes."""

    pdf_bytes: bytes
    pptx_bytes: bytes


def build_agency_deck(
    report: Any,
    client_name: str = "Client",
    brand_name: str = "Brand",
) -> DeckArtifacts:
    """Build PDF and PPTX deck from report."""
    # Placeholder implementation
    pdf_bytes = b"%PDF-1.4"
    pptx_bytes = b"PK"  # ZIP header

    return DeckArtifacts(pdf_bytes=pdf_bytes, pptx_bytes=pptx_bytes)


def _normalize_report_to_sections(report: Any) -> Dict[str, str]:
    """Normalize report to dict and extract sections."""

    def _to_mapping(obj: Any) -> Dict:
        if isinstance(obj, dict):
            return obj
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        if hasattr(obj, "__dict__"):
            return dict(obj.__dict__)
        return {}

    data = _to_mapping(report)

    CANDIDATES: Sequence[Tuple[str, str]] = [
        ("summary", "Executive Summary"),
        ("overview", "Executive Summary"),
        ("client_overview", "Client Overview"),
        ("brand_overview", "Brand Overview"),
        ("brand_audit", "Brand & Market Audit"),
        ("marketing_plan", "Strategic Marketing Plan"),
        ("strategy", "Strategy & Positioning"),
        ("campaign_blueprint", "Campaign Blueprint"),
        ("campaigns", "Campaign Concepts"),
        ("social_calendar", "30-Day Social Content Calendar"),
        ("content_calendar", "30-Day Content Plan"),
        ("performance_review", "Performance & KPIs"),
        ("measurement", "Measurement & Tracking"),
        ("creatives", "Key Creative Ideas"),
        ("creative_directions", "Creative Directions"),
        ("auto_detected_competitors", "Auto-Detected Competitors"),
        ("competitor_visual_benchmark", "Competitor Visual Benchmark"),
        ("recommendations", "Recommendations & Next Steps"),
        ("risks", "Risks & Assumptions"),
        ("appendix", "Appendix"),
        ("raw", "Full Report (Raw)"),
    ]

    sections: Dict[str, str] = {}

    for key, title in CANDIDATES:
        val = data.get(key)
        if val:
            sections[title] = str(val)

    return sections
