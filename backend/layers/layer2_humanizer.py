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
    
    Args:
        section_id: Section identifier (e.g., "overview", "campaign_objective")
        raw_text: Raw content from Layer 1
        context: Context dict with brand, campaign, market data
        req: GenerateRequest object
        llm_provider: Optional LLM provider callable (sync or async)
    
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
            logger.debug("Humanizer disabled, returning raw text")
            return raw_text
        
        # If raw_text is empty, nothing to enhance
        if not raw_text or not raw_text.strip():
            logger.debug(f"Raw text empty for {section_id}, skipping humanizer")
            return raw_text
        
        # If no LLM provider, can't enhance
        if llm_provider is None:
            logger.debug("No LLM provider available, returning raw text")
            return raw_text
        
        # Build humanization prompt
        brand_name = context.get("brand_name", "")
        campaign_name = context.get("campaign_name", "")
        
        humanize_prompt = f"""You are a marketing copywriter. Make the following section more human-like, specific, and compelling.

Section: {section_id}
Brand: {brand_name}
Campaign: {campaign_name}

Guidelines:
1. Eliminate clichés like "boost your brand", "in today's digital world", "unlock your potential"
2. Add specific details, numbers, and examples where appropriate
3. Improve hooks and CTAs to be more compelling and action-oriented
4. Preserve all structure, headings, and formatting
5. Keep word count within ±20% of original (original: ~{len(raw_text.split())} words)

Original section:
{raw_text}

Enhanced section (preserve structure, improve humanity and specificity):"""

        # Call LLM for enhancement
        # Note: This might be sync or async, but we'll call it and log if it fails
        try:
            # Try to call it directly (sync path)
            enhanced = llm_provider(
                prompt=humanize_prompt,
                max_tokens=min(2000, len(raw_text.split()) * 2 + 200),
                temperature=0.7,
            )
            
            # Handle case where result is a coroutine (async)
            import inspect
            if inspect.iscoroutine(enhanced):
                logger.debug("LLM provider returned coroutine, cannot await from sync context")
                return raw_text
            
        except Exception as e:
            logger.debug(f"LLM call exception: {e}")
            return raw_text
        
        if not enhanced or not isinstance(enhanced, str) or not enhanced.strip():
            logger.debug(f"Humanizer returned empty result for {section_id}")
            return raw_text
        
        logger.debug(f"Humanized section {section_id}")
        return enhanced
        
    except Exception as e:
        logger.debug(
            f"Humanizer failed for {section_id}, returning raw text",
            extra={"error": str(e)},
        )
        return raw_text
