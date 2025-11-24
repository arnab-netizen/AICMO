# aicmo/generators/output_formatter.py

"""
Output formatting and guardrails for AICMO generators.

This module provides utilities for:
1. Removing generic AI language patterns (FIX #5)
2. Enforcing consistent hierarchy and spacing (FIX #8)
3. Applying premium copywriting patterns (FIX #6)
"""

from __future__ import annotations
from typing import Optional
import re


def remove_generic_ai_patterns(text: str) -> str:
    """
    FIX #5: Remove generic AI markers that make text sound less human.

    Eliminates patterns like "in conclusion", "overall", "here are", etc.
    """
    BAD_MARKERS = [
        r"\bin conclusion\b",
        r"\boverall\b",
        r"\bhere are\b",
        r"\bthis report\b",
        r"\bto summarize\b",
        r"\bas mentioned\b",
        r"\badditionally\b",
        r"\bfurthermore\b",
        r"\bin other words\b",
        r"\bbasically\b",
        r"\bsimply put\b",
    ]

    for marker in BAD_MARKERS:
        text = re.sub(marker, "", text, flags=re.IGNORECASE)

    return text.strip()


def enforce_hierarchy_and_spacing(text: str) -> str:
    """
    FIX #8: Enforce consistent markdown hierarchy and spacing.

    - Normalize multiple blank lines to exactly 2
    - Ensure proper spacing around headers
    - Clean up trailing whitespace
    """
    # Normalize multiple blank lines (3+) to exactly 2
    text = re.sub(r"\n\n\n+", "\n\n", text)

    # Ensure blank line after headers
    text = re.sub(r"(^#{1,6}\s+[^\n]+)\n(?!\n)", r"\1\n\n", text, flags=re.MULTILINE)

    # Strip trailing whitespace from lines
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def format_final_output(text: str) -> str:
    """
    Apply all formatting guardrails to final output.

    Combines:
    - Generic AI pattern removal (FIX #5)
    - Hierarchy and spacing enforcement (FIX #8)
    """
    text = remove_generic_ai_patterns(text)
    text = enforce_hierarchy_and_spacing(text)
    return text


def apply_premium_copywriting_rules(text: str, copywriting_pattern: Optional[str] = None) -> str:
    """
    FIX #6: Apply premium copywriting recipes to text.

    Enhances hooks, angles, and messaging using:
    - Sensory language
    - Emotional drivers
    - Benefit-led framing

    Args:
        text: The text to enhance
        copywriting_pattern: Optional example pattern from training library

    Returns:
        Enhanced text with premium copywriting applied
    """
    # If we have a training pattern, use it as inspiration
    if copywriting_pattern:
        # Pattern can be used to understand premium style
        # For now, we apply basic premium copywriting rules
        pass

    # Premium language replacements (more aggressive than quality_enforcer)
    PREMIUM_REPLACEMENTS = {
        r"\bfeature\b": "capability",
        r"\bproblem\b": "challenge",
        r"\bbig\b": "significant",
        r"\bsmall\b": "boutique",
        r"\bfast\b": "rapid",
        r"\bslow\b": "deliberate",
        r"\bexpensive\b": "investment-grade",
        r"\bcheap\b": "accessible",
    }

    for pattern, replacement in PREMIUM_REPLACEMENTS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text
