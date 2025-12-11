"""
SWOT Analysis Generator.

Generates brief-specific SWOT (Strengths, Weaknesses, Opportunities, Threats)
for LLM/TURBO modes while providing a safe fallback for stub mode.
"""

import json
import logging
import os
from typing import Dict, List, Optional

from aicmo.io.client_reports import ClientInputBrief
from aicmo.presets.industry_presets import IndustryPreset

logger = logging.getLogger(__name__)


def generate_swot(
    brief: ClientInputBrief,
    industry_preset: Optional[IndustryPreset] = None,
    memory_snippets: Optional[List[str]] = None,
    max_items: int = 5,
) -> Dict[str, List[str]]:
    """
    Generate a brief-specific SWOT analysis using LLM.

    Args:
        brief: ClientInputBrief with brand, audience, category, goals, etc.
        industry_preset: Optional IndustryPreset for additional context.
        memory_snippets: Optional list of relevant Phase L memory snippets.
        max_items: Maximum number of bullets per quadrant (default: 5).

    Returns:
        Dict with keys: strengths, weaknesses, opportunities, threats.
        Each value is a list of non-empty strings.

    Behavior:
        - In LLM mode (AICMO_USE_LLM=1): Calls LLM to generate brief-specific SWOT.
        - On LLM failure: Falls back to a minimal, non-cringy template.
        - Always returns valid structure (4 keys, each a list).
    """
    # Check if LLM mode is enabled
    use_llm = os.getenv("AICMO_USE_LLM", "0") == "1"

    if not use_llm:
        # Stub mode: return minimal, neutral SWOT
        return _stub_swot(brief)

    # LLM mode: try to generate brief-specific SWOT
    try:
        llm_swot = _generate_swot_with_llm(brief, industry_preset, memory_snippets)
        if llm_swot:
            # Sanitize and enforce max_items
            return _sanitize_swot(llm_swot, max_items)
    except Exception as e:
        logger.warning(f"SWOT LLM generation failed: {e}", exc_info=False)

    # Fallback: minimal template (never throws, always returns valid structure)
    return _stub_swot(brief)


def _generate_swot_with_llm(
    brief: ClientInputBrief,
    industry_preset: Optional[IndustryPreset] = None,
    memory_snippets: Optional[List[str]] = None,
) -> Optional[Dict[str, List[str]]]:
    """
    Call the LLM to generate brief-specific SWOT using the Phase 8.4 router.

    Returns dict with strengths/weaknesses/opportunities/threats or None on failure.
    """
    try:
        # Import LLM router (Phase 8.4)
        from aicmo.llm.router import get_llm_client, LLMUseCase

        # Build the prompt
        brand_name = brief.brand.brand_name
        industry = brief.brand.industry or brief.brand.business_type or "their industry"
        audience = brief.audience.primary_customer or "their target audience"
        goals = brief.goal.primary_goal or "achieve business growth"
        timeline = brief.goal.timeline or "3 months"

        prompt = f"""
You are a senior marketing strategist analyzing a brand for SWOT.

Brand: {brand_name}
Industry: {industry}
Target Audience: {audience}
Primary Goal: {goals}
Timeline: {timeline}

Strengths: What advantages does {brand_name} have?
Weaknesses: What limitations or gaps does {brand_name} face?
Opportunities: What market or strategic openings exist?
Threats: What external risks or competitive pressures apply?

Return ONLY a valid JSON object with these exact keys:
{{
  "strengths": ["item1", "item2", ...],
  "weaknesses": ["item1", "item2", ...],
  "opportunities": ["item1", "item2", ...],
  "threats": ["item1", "item2", ...]
}}

Each item should be:
- 1-2 sentences, specific to {brand_name}
- Action-oriented or concrete
- No generic placeholders
- No "will be refined" or "TBD" language
""".strip()

        # Get LLM client for STRATEGY_DOC use-case (SWOT is part of strategy)
        chain = get_llm_client(
            use_case=LLMUseCase.STRATEGY_DOC,
            profile_override=None,
            deep_research=False,
            multimodal=False
        )

        # Call the chain via ProviderChain.invoke
        import asyncio
        success, result, provider_name = asyncio.run(
            chain.invoke(
                "generate",
                prompt=prompt
            )
        )

        if not success or not result:
            logger.warning(f"SWOT: LLM returned failure via {provider_name}")
            return None

        # Extract response text
        response_text = result if isinstance(result, str) else result.get("content", "")
        
        if not response_text:
            logger.warning("SWOT: LLM returned empty response")
            return None

        # Parse JSON
        swot_json = json.loads(response_text.strip())

        # Validate structure
        required_keys = {"strengths", "weaknesses", "opportunities", "threats"}
        if not all(key in swot_json for key in required_keys):
            logger.warning(f"SWOT: LLM JSON missing required keys. Got: {list(swot_json.keys())}")
            return None

        # Ensure all values are lists
        for key in required_keys:
            if not isinstance(swot_json[key], list):
                logger.warning(f"SWOT: Key '{key}' is not a list, got {type(swot_json[key])}")
                return None

        return swot_json

    except json.JSONDecodeError as e:
        logger.warning(f"SWOT: Failed to parse LLM response as JSON: {e}")
        return None
    except Exception as e:
        logger.warning(f"SWOT: LLM call failed: {e}", exc_info=False)
        return None


def _sanitize_swot(
    swot: Dict[str, List[str]],
    max_items: int = 5,
) -> Dict[str, List[str]]:
    """
    Sanitize SWOT structure: strip whitespace, enforce max_items, remove empties.

    Returns dict with same structure, all values as clean lists of strings.
    """
    result = {
        "strengths": [],
        "weaknesses": [],
        "opportunities": [],
        "threats": [],
    }

    for key in result.keys():
        raw_items = swot.get(key, [])
        if not isinstance(raw_items, list):
            raw_items = []

        # Clean each item: strip whitespace, skip empty
        cleaned = [str(item).strip() for item in raw_items if item and str(item).strip()]

        # Enforce max_items
        result[key] = cleaned[:max_items]

    return result


def _stub_swot(brief: ClientInputBrief) -> Dict[str, List[str]]:
    """
    Fallback SWOT for stub mode or LLM failures.

    Uses minimal, neutral bullets that don't make overpromising claims.
    No "will be refined", "placeholder", or obviously fake content.
    """
    brand_name = brief.brand.brand_name or "Your Brand"

    return {
        "strengths": [
            f"{brand_name} has clear objectives for growth.",
            "There is structured planning around brand positioning.",
        ],
        "weaknesses": [
            "Past marketing efforts may have lacked consistency.",
            "Channel presence could be more coordinated.",
        ],
        "opportunities": [
            "Build a recognizable brand narrative across channels.",
            "Establish a repeatable content system that compounds over time.",
        ],
        "threats": [
            "Competitors with more frequent marketing activity.",
            "Market and platform algorithm changes.",
        ],
    }
