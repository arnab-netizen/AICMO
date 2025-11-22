"""Bridge from AICMO objects to the memory engine."""

from __future__ import annotations

from typing import List, Optional, Tuple

from aicmo.io.client_reports import ClientInputBrief, AICMOOutputReport
from aicmo.memory.engine import (
    learn_from_blocks,
    augment_prompt_with_memory,
)


def _brief_to_text(brief: ClientInputBrief) -> str:
    """
    Convert ClientInputBrief to a compact text summary for embeddings.

    Adjust field names if your dataclass uses different names.
    """
    # Check if brief has a custom method
    if hasattr(brief, "to_prompt_string"):
        return brief.to_prompt_string()

    parts: List[str] = []

    # Collect available fields
    for field_name in (
        "brand_name",
        "brand_description",
        "industry",
        "category",
        "target_audience",
        "goals",
        "challenges",
        "tone",
    ):
        if hasattr(brief, field_name):
            value = getattr(brief, field_name)
            if value:
                parts.append(f"{field_name}: {value}")

    # Final fallback
    if not parts:
        parts.append(repr(brief))

    return "\n".join(parts)


def learn_from_report(
    report: AICMOOutputReport,
    project_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> int:
    """
    Flatten a finished AICMOOutputReport into text blocks and feed them into memory.

    Args:
        report: Completed AICMO report
        project_id: Optional project identifier
        tags: Optional list of tags

    Returns:
        Number of blocks stored
    """
    blocks: List[Tuple[str, str]] = []

    # Possible sections in AICMOOutputReport. Adjust if your structure uses different names.
    possible_sections = [
        ("Brand Strategy", "brand_strategy"),
        ("Audience & Segmentation", "audience"),
        ("Positioning & Narrative", "positioning"),
        ("Campaign Blueprint", "campaign_blueprint"),
        ("Content Strategy", "content_strategy"),
        ("Social Calendar", "social_calendar"),
        ("Performance Review", "performance_review"),
        ("Creative Directions", "creative_directions"),
        ("Key Messages", "key_messages"),
    ]

    for title, attr in possible_sections:
        if hasattr(report, attr):
            value = getattr(report, attr)
            if value:
                text = str(value).strip()
                if text:
                    blocks.append((title, text))

    if not blocks:
        # Fallback: store whole report as one block
        blocks.append(("Full Report", repr(report)))

    return learn_from_blocks(
        kind="report_section",
        blocks=blocks,
        project_id=project_id,
        tags=tags or ["auto_learn"],
    )


def augment_with_memory_for_brief(
    brief: ClientInputBrief,
    base_prompt: str,
) -> str:
    """
    Helper you can call from any generator to augment prompts with learned context.

    Usage:
        from backend.services.learning import augment_with_memory_for_brief
        prompt = build_strategy_prompt(brief, presets, ...)
        prompt = augment_with_memory_for_brief(brief, prompt)

    Args:
        brief: Client input brief
        base_prompt: Original prompt to augment

    Returns:
        Augmented prompt with learned context, or original if no matches
    """
    brief_text = _brief_to_text(brief)
    return augment_prompt_with_memory(brief_text=brief_text, base_prompt=base_prompt)
