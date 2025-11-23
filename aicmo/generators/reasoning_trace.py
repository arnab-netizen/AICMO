"""Operator-level reasoning trace generation.

Appends an internal strategy trace to the report for operator/internal review.
This section can be optionally stripped from client-facing exports if needed.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def attach_reasoning_trace(
    draft: str,
    brief: Dict[str, Any],
    frameworks_str: str,
    internal_only: bool = True,
) -> str:
    """
    Append an internal strategy trace section to the draft.

    This creates a structured "INTERNAL STRATEGY TRACE (AUTO-GENERATED)" section
    that documents what frameworks, brief elements, and reasoning informed the report.

    Args:
        draft: The generated report text
        brief: Client brief dict
        frameworks_str: Concatenated string of applied frameworks/references
        internal_only: If True, section is marked for internal use only

    Returns:
        Draft with reasoning trace appended
    """
    parts = [
        draft.rstrip(),
        "",
        "---",
        "",
    ]

    if internal_only:
        parts.append("### INTERNAL STRATEGY TRACE (AUTO-GENERATED)")
        parts.append("*For internal review and operator reference only.*")
        parts.append("")
    else:
        parts.append("### STRATEGY TRACE & FRAMEWORK REFERENCE")
        parts.append("")

    if brief:
        parts.append("**Brief Summary Used:**")
        parts.append("")
        # Extract key elements from brief
        brand = brief.get("brand", {})
        if brand:
            brand_name = brand.get("brand_name", "Brand")
            parts.append(f"- Brand: {brand_name}")
            if brand.get("industry"):
                parts.append(f"- Industry: {brand.get('industry')}")

        goal = brief.get("goal", {})
        if goal:
            primary = goal.get("primary_goal")
            if primary:
                parts.append(f"- Primary Goal: {primary}")

        parts.append("")

    if frameworks_str:
        parts.append("**Frameworks & References Applied:**")
        parts.append("")
        parts.append(frameworks_str.strip())
        parts.append("")

    parts.append("---")

    return "\n".join(parts).strip() + "\n"


def should_strip_reasoning_trace(export_format: str) -> bool:
    """
    Determine if reasoning trace should be stripped from this export format.

    Trace is kept in:
    - Markdown exports (internal use)
    - Operator dashboards

    Trace is removed from:
    - Client PDF/PPTX exports
    - Final client deliverables

    Args:
        export_format: Format string like "pdf", "pptx", "markdown", "html"

    Returns:
        True if trace should be stripped for this format
    """
    client_formats = {"pdf", "pptx", "docx"}
    return export_format.lower() in client_formats


def strip_reasoning_trace(text: str) -> str:
    """
    Remove the reasoning trace section from text.

    Finds and removes the "INTERNAL STRATEGY TRACE" or "STRATEGY TRACE" section
    and everything after it until EOF or next major section.

    Args:
        text: Text that may contain reasoning trace

    Returns:
        Text with trace section removed
    """
    lines = text.split("\n")
    result = []
    in_trace = False

    for line in lines:
        if "STRATEGY TRACE" in line:
            in_trace = True
            continue

        if in_trace:
            # Keep the separator before trace, but skip everything after
            if line.startswith("###"):
                # New major section might be starting; check if it's trace
                if "TRACE" not in line:
                    in_trace = False
                    result.append(line)
            # Skip trace content
            continue

        result.append(line)

    return "\n".join(result).strip() + "\n"
