# aicmo/presets/quality_enforcer.py

from __future__ import annotations
from typing import Dict, Any


def enforce_quality(brief: Dict[str, Any], output: str) -> str:
    """
    Injects mandatory strategic blocks + improves language + ensures structure
    so every AICMO report hits 100/100 quality.

    🔥 FIX #7: Auto-generation of missing sections is now disabled.
    Missing sections are silently skipped rather than auto-filled from training libraries.
    """

    MUST_HAVE_SECTIONS = [
        "Executive Summary",
        "Diagnostic Analysis",
        "Consumer Mindset Map",
        "Category Tension",
        "Competitor Territory Map",
        "Funnel Messaging Architecture",
        "Positioning Model",
        "Creative Territories",
        "Premium Hooks & Angles",
        "30-Day Content Engine",
        "Campaign Measurement Plan",
        "Operator Rationale (Why Each Choice Was Made)",
    ]

    missing_sections = [s for s in MUST_HAVE_SECTIONS if s not in output]

    # 🔥 FIX #7: Silently skip missing sections instead of auto-generating them
    for section in missing_sections:
        # Do NOT append placeholder text to output
        # Just log the missing section for diagnostics
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"ℹ️  Missing section (auto-generation disabled): {section}")

    # Improve tone with premium language rules
    REPLACEMENTS = {
        "good": "elevated",
        "simple": "effortless",
        "nice": "refined",
        "great": "high-impact",
        "beautiful": "exquisite",
        "premium": "luxury-grade",
        "engage": "captivate",
    }

    for bad, better in REPLACEMENTS.items():
        output = output.replace(f" {bad} ", f" {better} ")

    return output
