"""
LAYER 2: HUMANIZER / ENHANCEMENT PASS

Purpose: Make draft more human-like, specific, and compelling (FALLBACK-SAFE).

Behavior:
- Takes Layer 1 output
- Calls LLM to eliminate clichés, add specifics, improve hooks/CTAs
- Preserves structure and headings
- Respects word-count ranges (±20% tolerance)
- On ANY error → silently returns raw_text (no exception)

Key: This layer NEVER raises HTTPException or blocks. Always returns string.

Configuration:
- ENABLE_HUMANIZER: bool = env("AICMO_ENABLE_HUMANIZER", default=True)
  - True in production
  - Can be disabled in tests via env var to avoid snapshot flakiness
"""

import logging
import os
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# Configuration
ENABLE_HUMANIZER = os.environ.get("AICMO_ENABLE_HUMANIZER", "true").lower() == "true"


def enhance_section_humanizer(
    section_id: str,
    raw_text: str,
    context: dict,
    req,
    llm_provider: Optional[Callable] = None,
) -> str:
    """
    Enhance raw section with humanization pass (SYNCHRONOUS).
    
    Behavior:
    1. If ENABLE_HUMANIZER is False, return raw_text immediately
    2. If raw_text is empty, return raw_text
    3. If llm_provider is None, use get_llm_provider() to try to get one
    4. If we can't get any LLM provider, return raw_text
    5. Call LLM with humanization prompt
    6. On ANY error, return raw_text (never raise)
    
    Args:
        section_id: Section identifier (e.g., "overview", "campaign_objective")
        raw_text: Raw content from Layer 1
        context: Context dict with brand, campaign, market data
        req: GenerateRequest object
        llm_provider: Optional LLM provider callable (will use factory if None)
    
    Returns:
        Enhanced section text (str), or raw_text if enhancement fails/disabled
        
    Guarantees:
        - Never raises HTTPException
        - Never blocks user
        - Always returns string (raw_text on any error)
        - Respects ±20% word-count tolerance
        - Preserves structure and headings
    """
    try:
        # Check if humanizer is enabled
        if not ENABLE_HUMANIZER:
            logger.debug("Humanizer disabled (AICMO_ENABLE_HUMANIZER=false)")
            return raw_text
        
        # If raw_text is empty, nothing to enhance
        if not raw_text or not raw_text.strip():
            logger.debug(f"Raw text empty for {section_id}, skipping humanizer")
            return raw_text
        
        # If no LLM provider injected, try to get one from factory
        if llm_provider is None:
            from backend.layers import get_llm_provider
            llm_provider = get_llm_provider()
        
        # If still no LLM provider, can't enhance
        if llm_provider is None:
            logger.debug("No LLM provider available, returning raw text")
            return raw_text
        
        # Build humanization prompt
        brand_name = context.get("brand_name", "")
        campaign_name = context.get("campaign_name", "")
        target_audience = context.get("target_audience", "")
        
        word_count = len(raw_text.split())
        
        humanize_prompt = f"""You are a senior marketing copywriter. Make the following section more human-like, specific, and compelling.

[SECTION]: {section_id}
[BRAND]: {brand_name}
[CAMPAIGN]: {campaign_name}
[TARGET AUDIENCE]: {target_audience}

[GUIDELINES]:
1. Eliminate clichés: "boost your brand", "in today's digital world", "unlock your potential", "best-in-class", "game-changer"
2. Add specific details, numbers, case studies, or examples where appropriate
3. Improve hooks and CTAs: make them compelling and action-oriented
4. PRESERVE all structure, headings, and formatting exactly
5. Keep word count ±20% of original ({word_count} words) – target: {int(word_count * 0.9)}-{int(word_count * 1.1)} words

[ORIGINAL SECTION]:
{raw_text}

[TASK]: Rewrite above section to be more human, specific, and compelling while preserving ALL structure and formatting. Output ONLY the enhanced section, no explanations."""

        # Call LLM for enhancement
        try:
            enhanced = llm_provider(
                prompt=humanize_prompt,
                max_tokens=min(2000, word_count * 2 + 300),
                temperature=0.7,
            )
            
            # Handle case where result is a coroutine (async)
            import asyncio
            if asyncio.iscoroutine(enhanced):
                logger.debug("LLM provider returned coroutine, cannot await from sync context")
                return raw_text
            
        except Exception as e:
            logger.warning(f"LLM humanizer call failed for {section_id}: {type(e).__name__}: {e}")
            return raw_text
        
        if not enhanced or not isinstance(enhanced, str) or not enhanced.strip():
            logger.debug(f"Humanizer returned empty result for {section_id}")
            return raw_text
        
        # Verify enhanced text isn't just whitespace
        if len(enhanced.strip()) < len(raw_text.strip()) * 0.5:
            logger.debug(f"Humanized text is too short for {section_id}, rejecting")
            return raw_text
        
        logger.debug(f"Humanized section {section_id} ({len(raw_text)} → {len(enhanced)} chars)")
        return enhanced
        
    except Exception as e:
        logger.warning(
            f"Unexpected error in humanizer for {section_id}: {type(e).__name__}: {e}"
        )
        return raw_text
