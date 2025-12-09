"""
LAYER 1: RAW DRAFT GENERATOR

Purpose: Generate first-pass draft with correct structure (UNBLOCKED).

Behavior:
- Calls existing SECTION_GENERATORS[section_id]
- Uses improved prompts with explicit outline + word-count ranges (not exact counts)
- No validation, no exceptions
- Returns raw content or empty string

Key: This layer NEVER raises HTTPException. Any error returns empty string.
"""

import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)


def generate_raw_section(
    section_id: str,
    context: dict,
    req,
    section_generators: dict,
) -> str:
    """
    Generate a raw first-pass section using existing generators (SYNCHRONOUS).
    
    Args:
        section_id: Section identifier (e.g., "overview", "campaign_objective")
        context: Context dict with brand, campaign, market data
        req: GenerateRequest object with pack_key, tone, other config
        section_generators: SECTION_GENERATORS dict from main.py
    
    Returns:
        Raw section text (str), or empty string if generation fails
        
    Guarantees:
        - Never raises HTTPException
        - Never blocks user
        - Always returns string (empty if error)
    """
    try:
        if section_id not in section_generators:
            logger.warning(f"Unknown section_id: {section_id}, returning empty string")
            return ""
        
        generator_fn = section_generators[section_id]
        
        # Call the generator
        try:
            result = generator_fn(context, req)
            
            # Handle async functions by checking if they return a coroutine
            if asyncio.iscoroutine(result):
                # We're in a sync context, so we can't await
                # This shouldn't happen if generators are sync, but just in case:
                logger.debug(f"Generator {section_id} returned async coroutine (unexpected in sync context)")
                result.close()  # Clean up the coroutine
                return ""
            
            return result if isinstance(result, str) else ""
            
        except Exception as e:
            logger.debug(
                f"Generator {section_id} failed",
                extra={"section_id": section_id, "error": str(e)},
            )
            return ""
            
    except Exception as e:
        logger.error(
            f"Unexpected error in generate_raw_section",
            extra={"section_id": section_id, "error": str(e)},
            exc_info=True,
        )
        return ""
