"""
Parse WOW markdown documents into structured sections for validation.

This module solves Bug #2 (type mismatch) by converting the single markdown
string returned by build_wow_report() into the List[Dict[str, str]] format
expected by validate_report_sections().
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


def parse_wow_markdown_to_sections(wow_markdown: str) -> List[Dict[str, str]]:
    """
    Parse a complete WOW markdown document into individual sections.

    This function extracts sections from a WOW report by splitting on level-2
    markdown headers (## Section Name). Each section includes its header and
    all content until the next header.

    Args:
        wow_markdown: Complete WOW markdown document as a single string

    Returns:
        List of section dictionaries with 'id' and 'content' keys:
        [
            {"id": "overview", "content": "## Overview\n\nBrand: ..."},
            {"id": "messaging_framework", "content": "## Messaging Framework\n\n..."}
        ]

    Example:
        >>> markdown = "## Overview\\n\\nBrand: ACME\\n\\n## Messaging\\n\\nKey message"
        >>> sections = parse_wow_markdown_to_sections(markdown)
        >>> len(sections)
        2
        >>> sections[0]["id"]
        'overview'
    """
    if not wow_markdown or not wow_markdown.strip():
        logger.warning("parse_wow_markdown_to_sections called with empty markdown")
        return []

    sections: List[Dict[str, str]] = []
    current_section_id: str | None = None
    current_lines: List[str] = []

    for line in wow_markdown.split("\n"):
        # Check for level-2 header (## Section Name)
        header_match = re.match(r"^##\s+(.+)$", line)

        if header_match:
            # Save previous section before starting new one
            if current_section_id is not None:
                sections.append(
                    {"id": current_section_id, "content": "\n".join(current_lines).strip()}
                )

            # Start new section
            section_title = header_match.group(1).strip()
            current_section_id = _title_to_section_id(section_title)
            current_lines = [line]  # Include header in content

        else:
            # Accumulate lines for current section
            if current_section_id is not None:
                current_lines.append(line)
            else:
                # Content before first header - treat as preamble
                if line.strip():
                    logger.debug(f"Skipping preamble content: {line[:50]}...")

    # Don't forget the last section
    if current_section_id is not None:
        sections.append({"id": current_section_id, "content": "\n".join(current_lines).strip()})

    logger.info(
        "WOW_MARKDOWN_PARSED",
        extra={
            "total_sections": len(sections),
            "section_ids": [s["id"] for s in sections],
            "total_chars": len(wow_markdown),
        },
    )

    return sections


def _title_to_section_id(title: str) -> str:
    """
    Convert a section title to a section ID.

    Normalizes titles to match the section IDs used in WOW rules and benchmarks.

    Examples:
        "Client Overview" -> "overview"
        "5. Hashtag Strategy" -> "hashtag_strategy"
        "30-Day Social Calendar" -> "detailed_30_day_calendar"
        "Messaging Framework" -> "messaging_framework"
        "KPI Plan" -> "kpi_plan_light"

    Args:
        title: Human-readable section title from markdown header

    Returns:
        Normalized section ID (lowercase, underscores, special cases handled)
    """
    # Strip leading numbers and periods (e.g., "5. Hashtag Strategy" -> "Hashtag Strategy")
    title = re.sub(r"^\d+\.\s*", "", title)

    # Normalize: lowercase, replace spaces/hyphens with underscores
    normalized = title.lower().replace(" ", "_").replace("-", "_")

    # Remove special characters
    normalized = re.sub(r"[^\w_]", "", normalized)

    # Clean up multiple underscores
    normalized = re.sub(r"_+", "_", normalized).strip("_")

    # Handle special mappings to match benchmark IDs
    mappings = {
        "client_overview": "overview",
        "brand_snapshot": "overview",
        "brand_context_snapshot": "overview",
        "campaign_overview": "overview",  # strategy_campaign_standard
        "campaign_objectives": "campaign_objective",  # plural -> singular
        "30_day_social_calendar": "detailed_30_day_calendar",
        "30_day_content_calendar": "detailed_30_day_calendar",
        "social_calendar": "detailed_30_day_calendar",
        "kpi_plan": "kpi_plan_light",
        "kpis_lightweight_measurement_plan": "kpi_plan_light",
        "kpi_budget_plan": "kpi_and_budget_plan",  # missing "and"
        "promotions_offers": "promotions_and_offers",  # missing "and"
        "email_crm_flows": "email_and_crm_flows",  # missing "and"
        "final_summary": "final_summary",
        "final_summary_next_steps": "final_summary",
        "next_steps": "final_summary",
        "content_buckets_themes": "content_buckets",
    }

    return mappings.get(normalized, normalized)


def validate_section_completeness(
    sections: List[Dict[str, str]], expected_section_ids: List[str]
) -> Dict[str, bool]:
    """
    Check if all expected sections are present in parsed output.

    Args:
        sections: Parsed sections from parse_wow_markdown_to_sections()
        expected_section_ids: Section IDs that should be present (from WOW rule)

    Returns:
        Dictionary mapping section_id -> is_present (bool)

    Example:
        >>> sections = [{"id": "overview", "content": "..."}]
        >>> expected = ["overview", "messaging_framework"]
        >>> result = validate_section_completeness(sections, expected)
        >>> result
        {'overview': True, 'messaging_framework': False}
    """
    parsed_ids = {s["id"] for s in sections}
    return {section_id: section_id in parsed_ids for section_id in expected_section_ids}
