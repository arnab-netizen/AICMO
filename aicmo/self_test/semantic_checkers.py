"""
Semantic Alignment Checker

Checks semantic alignment between ClientInputBrief and generator outputs.
Identifies obvious mismatches (e.g., wrong industry, missing goals).
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from aicmo.io.client_reports import ClientInputBrief

logger = logging.getLogger(__name__)


@dataclass
class SemanticAlignmentResult:
    """Result of semantic alignment check."""
    is_valid: bool = True
    mismatched_fields: List[str] = field(default_factory=list)
    partial_matches: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


def _extract_keywords(text: Optional[str]) -> set[str]:
    """Extract lowercase keywords from text."""
    if not text:
        return set()
    # Simple tokenization: lowercase, split on whitespace/punctuation
    text = text.lower()
    # Remove common punctuation
    text = text.replace(",", " ").replace(".", " ").replace(";", " ")
    text = text.replace("(", " ").replace(")", " ").replace("-", " ")
    words = [w.strip() for w in text.split() if w.strip()]
    return set(words)


def _keyword_overlap(text1: Optional[str], text2: Optional[str], min_overlap: int = 1) -> bool:
    """Check if text1 and text2 share at least min_overlap keywords."""
    keys1 = _extract_keywords(text1)
    keys2 = _extract_keywords(text2)
    overlap = keys1 & keys2
    return len(overlap) >= min_overlap


def _contains_keywords(haystack: Optional[str], needle_list: List[str]) -> bool:
    """Check if haystack contains any keyword from needle_list."""
    if not haystack or not needle_list:
        return False
    haystack_lower = haystack.lower()
    for needle in needle_list:
        if needle.lower() in haystack_lower:
            return True
    return False


def _extract_text_from_output(output: Any, max_depth: int = 3, current_depth: int = 0) -> str:
    """
    Recursively extract all text from output (dict, list, or Pydantic model).
    Joins all text fields into a single searchable string.
    """
    if current_depth >= max_depth:
        return ""

    text_parts = []

    # Handle Pydantic models
    if hasattr(output, "model_dump"):
        try:
            output = output.model_dump()
        except Exception:
            return str(output)

    # Handle dicts
    if isinstance(output, dict):
        for key, value in output.items():
            if isinstance(value, str) and value.strip():
                text_parts.append(value)
            elif isinstance(value, (dict, list)):
                text_parts.append(
                    _extract_text_from_output(value, max_depth, current_depth + 1)
                )

    # Handle lists
    elif isinstance(output, list):
        for item in output[:20]:  # Limit to first 20 items
            if isinstance(item, str) and item.strip():
                text_parts.append(item)
            elif isinstance(item, (dict, list)):
                text_parts.append(
                    _extract_text_from_output(item, max_depth, current_depth + 1)
                )

    # Handle strings
    elif isinstance(output, str):
        return output

    return " ".join(text_parts)


def check_semantic_alignment(
    brief: ClientInputBrief, output: Any, feature_name: str
) -> SemanticAlignmentResult:
    """
    Check semantic alignment between brief and generator output.

    Simple heuristics (no LLM):
    1. Industry keywords from brief should appear in output
    2. Primary goal keywords should appear in strategy/recommendations
    3. Audience/persona segments should roughly match
    4. Product/service keywords should be present in relevant outputs

    Returns SemanticAlignmentResult with any detected mismatches.
    """
    result = SemanticAlignmentResult(is_valid=True)

    # Extract all text from output
    output_text = _extract_text_from_output(output)

    # Normalize for comparison
    output_lower = output_text.lower()

    # =========================================================================
    # 1. Check Industry Keywords
    # =========================================================================
    industry = brief.brand.industry or ""
    if industry:
        industry_keywords = _extract_keywords(industry)
        if industry_keywords:
            # Check if any industry keyword appears in output
            found_industry = any(kw in output_lower for kw in industry_keywords)
            if not found_industry and len(industry) > 3:
                # Major mismatch: industry should be mentioned
                result.mismatched_fields.append(
                    f"Industry '{industry}' not mentioned in {feature_name}"
                )
                result.notes.append(
                    f"Output should contain references to '{industry}' industry context"
                )

    # =========================================================================
    # 2. Check Primary Goal Keywords
    # =========================================================================
    primary_goal = brief.goal.primary_goal or ""
    if primary_goal and len(primary_goal) > 5:
        goal_keywords = _extract_keywords(primary_goal)
        # Remove common filler words
        goal_keywords = {w for w in goal_keywords if len(w) > 2}
        if goal_keywords:
            found_goal = any(kw in output_lower for kw in goal_keywords)
            if not found_goal:
                result.partial_matches.append(
                    f"Primary goal keywords not strongly reflected in {feature_name}"
                )
                result.notes.append(
                    f"Expected strategy to reference goal: '{primary_goal}'"
                )

    # =========================================================================
    # 3. Check Product/Service Keywords
    # =========================================================================
    product_service = brief.brand.product_service or ""
    if product_service and len(product_service) > 5:
        product_keywords = _extract_keywords(product_service)
        product_keywords = {w for w in product_keywords if len(w) > 2}
        if product_keywords:
            found_product = any(kw in output_lower for kw in product_keywords)
            if not found_product:
                result.partial_matches.append(
                    f"Product/service context not reflected in {feature_name}"
                )
                result.notes.append(
                    f"Consider mentioning: '{product_service}'"
                )

    # =========================================================================
    # 4. Persona-specific checks (for persona_generator output)
    # =========================================================================
    if feature_name.lower() in ["persona_generator", "persona", "audience"]:
        primary_customer = brief.audience.primary_customer or ""
        if primary_customer and len(primary_customer) > 5:
            customer_keywords = _extract_keywords(primary_customer)
            customer_keywords = {w for w in customer_keywords if len(w) > 2}
            if customer_keywords:
                found_customer = any(kw in output_lower for kw in customer_keywords)
                if not found_customer:
                    result.partial_matches.append(
                        f"Primary customer segment '{primary_customer}' not reflected in persona"
                    )
                    result.notes.append(
                        f"Persona should target: '{primary_customer}'"
                    )

    # =========================================================================
    # 5. Strategy-specific checks (for strategy, messaging, calendar)
    # =========================================================================
    if feature_name.lower() in [
        "situation_analysis_generator",
        "strategy",
        "messaging_pillars_generator",
        "social_calendar_generator",
        "calendar",
    ]:
        # Check if primary goal is addressed
        if primary_goal and not _keyword_overlap(primary_goal, output_text, min_overlap=1):
            result.notes.append(
                f"Strategy may not adequately address primary goal: '{primary_goal}'"
            )

        # Check if audience is addressed
        primary_customer = brief.audience.primary_customer or ""
        if primary_customer and not _keyword_overlap(primary_customer, output_text, min_overlap=1):
            result.partial_matches.append(
                f"Strategy does not explicitly reference audience: '{primary_customer}'"
            )

    # =========================================================================
    # 6. Check for blatant mismatches (red flags)
    # =========================================================================
    # Look for obvious contradictions in certain feature outputs
    if feature_name.lower() in ["social_calendar_generator", "calendar"]:
        # Calendars should have some temporal/platform references
        if "post" not in output_lower and "content" not in output_lower:
            result.notes.append(
                f"Calendar output lacks platform/content references (unexpected for {feature_name})"
            )

    # Set validity based on severity of mismatches
    if result.mismatched_fields:
        result.is_valid = False

    return result
