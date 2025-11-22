"""Bridge from AICMO objects to the memory engine."""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from aicmo.io.client_reports import ClientInputBrief, AICMOOutputReport
from aicmo.memory.engine import (
    learn_from_blocks,
    augment_prompt_with_memory,
)

logger = logging.getLogger("aicmo.learning")


# ============================================================
# SECTION MAPPING: Maps report field names to learning titles
# ============================================================
# This defines which sections of AICMOOutputReport to learn.
# Must match actual field names in AICMOOutputReport (checked at runtime).
SECTION_MAPPING = [
    ("Marketing Plan", "marketing_plan"),
    ("Campaign Blueprint", "campaign_blueprint"),
    ("Social Calendar", "social_calendar"),
    ("Performance Review", "performance_review"),
    ("Creatives", "creatives"),
    ("Persona Cards", "persona_cards"),
    ("Action Plan", "action_plan"),
]


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

    Design:
        - Uses SECTION_MAPPING to know which fields to extract
        - Gracefully skips missing or invalid fields (logs warning)
        - Falls back to full report if no sections found
        - Non-blocking: errors are logged but don't crash the caller
    """
    if not report:
        logger.warning("learn_from_report called with None report")
        return 0

    blocks: List[Tuple[str, str]] = []

    # Extract each section defined in SECTION_MAPPING
    for title, attr_name in SECTION_MAPPING:
        try:
            # Check if attribute exists on report
            if not hasattr(report, attr_name):
                logger.warning(f"learn_from_report: report missing attribute '{attr_name}'")
                continue

            # Get the value
            value = getattr(report, attr_name, None)
            if value is None:
                continue  # Skip None values silently

            # Convert to text
            text = str(value).strip()
            if text:
                blocks.append((title, text))
                logger.debug(f"learn_from_report: extracted {len(text)} chars from '{title}'")

        except Exception as e:
            # Log but continue – non-blocking
            logger.warning(f"learn_from_report: error extracting '{attr_name}': {e}")
            continue

    if not blocks:
        # Fallback: store whole report as one block
        logger.info("learn_from_report: no sections extracted, storing full report")
        blocks.append(("Full Report", str(report)))

    # Store in memory engine
    stored_count = learn_from_blocks(
        kind="report_section",
        blocks=blocks,
        project_id=project_id,
        tags=tags or ["auto_learn"],
    )

    logger.info(f"learn_from_report: stored {stored_count} blocks from {len(blocks)} sections")
    return stored_count


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
