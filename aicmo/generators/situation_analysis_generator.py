"""
Situation Analysis generator: brief-driven, LLM-capable, with safe stub fallback.

Replaces hardcoded template with dynamic generation based on brief content.
"""

import os
from typing import Optional

from aicmo.io.client_reports import ClientInputBrief


def generate_situation_analysis(
    brief: ClientInputBrief,
    industry_preset: Optional[dict] = None,
    memory_snippets: Optional[list] = None,
    max_paragraphs: int = 3,
) -> str:
    """
    Generate a brief-specific Situation Analysis.

    Automatically selects stub or LLM mode based on AICMO_USE_LLM.
    Always returns a non-empty string (graceful degradation).

    Args:
        brief: ClientInputBrief with brand, audience, goals, etc.
        industry_preset: Optional industry context dict
        memory_snippets: Optional list of relevant memory/learning snippets
        max_paragraphs: Max paragraphs to include (default 3)

    Returns:
        Non-empty string with Situation Analysis text (never throws)
    """
    try:
        use_llm = os.environ.get("AICMO_USE_LLM", "0").lower() in ["1", "true", "yes"]

        if use_llm:
            llm_result = _generate_situation_analysis_with_llm(
                brief, industry_preset, memory_snippets
            )
            if llm_result:
                return _sanitize_situation_analysis(llm_result, max_paragraphs)

        # Fall back to stub if LLM disabled or errored
        return _stub_situation_analysis(brief)

    except Exception:
        # Ultimate fallback: return stub even if something goes wrong
        return _stub_situation_analysis(brief)


def _generate_situation_analysis_with_llm(
    brief: ClientInputBrief,
    industry_preset: Optional[dict],
    memory_snippets: Optional[list],
) -> Optional[str]:
    """
    Generate Situation Analysis using LLM (Claude/OpenAI).

    Returns:
        Generated text string, or None if LLM call fails
    """
    try:
        # Lazy import to avoid hard dependency
        from aicmo.llm.client import get_llm_response

        brand_name = brief.brand.brand_name
        category = brief.brand.industry
        audience = brief.audience.primary_customer
        goals = brief.goal.primary_goal or "unspecified"
        timeline = brief.goal.timeline or "ongoing"

        # Build prompt
        prompt = f"""Generate a 2-3 paragraph Situation Analysis for a marketing plan.

Brand: {brand_name}
Category: {category}
Target Audience: {audience}
Primary Goal: {goals}
Timeline: {timeline}

Focus on:
1. Current market position and context relevant to this brand
2. The target audience's needs and pain points
3. The opportunity for this brand to address those needs

Keep language honest and grounded in the brief details provided.
Avoid placeholder phrases like "will be refined", "TBD", or "to be determined".
Avoid presumptive claims (e.g., "leading", "dominates", "stronger than competitors").

Generate only the analysis text itself, no headers or formatting."""

        result = get_llm_response(prompt, max_tokens=800)
        return result if result and result.strip() else None

    except Exception:
        return None


def _sanitize_situation_analysis(text: str, max_paragraphs: int = 3) -> str:
    """
    Sanitize and limit Situation Analysis output.

    - Splits on double newlines to find paragraphs
    - Removes paragraphs shorter than 20 characters
    - Enforces max_paragraphs limit
    - Strips whitespace

    Args:
        text: Raw analysis text
        max_paragraphs: Maximum number of paragraphs to keep

    Returns:
        Cleaned, limited analysis text
    """
    if not text or not text.strip():
        return ""

    # Split on double newlines to find paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n")]

    # Filter: keep only paragraphs with substantial content (>20 chars)
    filtered = [p for p in paragraphs if len(p) > 20]

    # Limit to max_paragraphs
    limited = filtered[:max_paragraphs]

    # Rejoin and strip
    result = "\n\n".join(limited).strip()
    return result


def _stub_situation_analysis(brief: ClientInputBrief) -> str:
    """
    Fallback: Generate minimal, honest Situation Analysis from brief alone.

    No placeholder phrases, no fake claims.
    Just factual, modest description of what the brief tells us.

    Args:
        brief: ClientInputBrief

    Returns:
        Non-empty string with brief-based analysis
    """
    brand_name = brief.brand.brand_name
    category = brief.brand.industry
    audience = brief.audience.primary_customer
    goals = brief.goal.primary_goal or "growth"
    timeline = brief.goal.timeline or "near term"

    # Build honest, brief-based analysis
    analysis = f"""{brand_name} operates in the {category} space, targeting {audience}. 

The primary objective is {goals} within the {timeline} timeframe. Key considerations include the audience's core pain points and how {brand_name} can deliver measurable value. Strategic positioning and competitive context are developed through market research and data-driven insights.

This foundation enables consistent, value-driven messaging that compounds over time and builds brand credibility."""

    return _sanitize_situation_analysis(analysis)
