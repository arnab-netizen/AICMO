"""
4-Layer Generation Pipeline for AICMO Pack Outputs

This module implements a progressive, non-blocking quality improvement pipeline:

Layer 1: Raw Draft Generator (UNBLOCKED)
  - Generates first-pass section content with correct structure
  - Never fails; returns raw text or empty string
  
Layer 2: Humanizer / Enhancement Pass (FALLBACK-SAFE)
  - Makes draft more human-like, specific, and compelling
  - On any error → silently returns raw_text (never blocks)
  
Layer 3: Soft Validators (NON-BLOCKING)
  - Scores and flags issues (quality, genericity, warnings)
  - Returns tuple: (text, quality_score, genericity_score, warnings)
  - Never raises HTTPException; all errors logged internally
  
Layer 4: Section-Level Rewriter (OPTIONAL, NON-BLOCKING)
  - Improves weak sections (quality_score < 60)
  - Max 1 rewrite attempt per section
  - On any error → returns previous version (never blocks)

Key Principles:
✅ Never blocks users (all errors handled gracefully)
✅ Backward compatible (all public APIs unchanged)
✅ Progressive enhancement (each layer improves previous output)
✅ Non-blocking validation (quality scored, not enforced)
✅ Safe social calendar (per-day fallback micro-passes)
✅ Comprehensive logging (warnings for low quality, debug for details)
✅ LLM optional and injectable (Layers 2 & 4 gracefully skip without LLM)
"""

import logging
import os
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)

from backend.layers.layer1_raw_draft import generate_raw_section
from backend.layers.layer2_humanizer import enhance_section_humanizer
from backend.layers.layer3_soft_validators import run_soft_validators
from backend.layers.layer4_section_rewriter import rewrite_low_quality_section

__all__ = [
    "generate_raw_section",
    "enhance_section_humanizer",
    "run_soft_validators",
    "rewrite_low_quality_section",
    "get_llm_provider",
]


def get_llm_provider() -> Optional[Callable]:
    """
    Factory function to get LLM provider for Layers 2 & 4.
    
    Supports:
    - Claude Sonnet 4 (via Anthropic SDK)
    - OpenAI GPT-4o-mini (via OpenAI SDK)
    
    Environment variables:
    - AICMO_LLM_PROVIDER: "claude" (default) or "openai"
    - ANTHROPIC_API_KEY: Claude API key
    - OPENAI_API_KEY: OpenAI API key
    
    Returns:
        Callable LLM provider function, or None if no LLM configured
        
    The provider callable accepts:
        - prompt (str): The prompt to send to LLM
        - max_tokens (int): Max tokens to generate
        - temperature (float): Sampling temperature
    
    Returns:
        Generated text (str) or original text on error (never raises)
    """
    try:
        provider_name = os.getenv("AICMO_LLM_PROVIDER", "claude").lower()
        
        if provider_name == "claude":
            try:
                from aicmo.llm.client import _get_claude_client, _rewrite_text_block
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    logger.debug("ANTHROPIC_API_KEY not set, LLM provider unavailable")
                    return None
                
                client = _get_claude_client()
                
                def claude_provider(prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
                    """Claude Sonnet 4 provider."""
                    try:
                        response = client.messages.create(
                            model="claude-3-5-sonnet-20241022",
                            max_tokens=max_tokens,
                            temperature=temperature,
                            messages=[{"role": "user", "content": prompt}],
                        )
                        if response.content and len(response.content) > 0:
                            return response.content[0].text
                        return ""
                    except Exception as e:
                        logger.debug(f"Claude LLM error: {e}")
                        return ""
                
                logger.debug("Claude Sonnet 4 provider initialized")
                return claude_provider
                
            except ImportError:
                logger.debug("Anthropic SDK not installed, trying OpenAI fallback")
                provider_name = "openai"
        
        if provider_name == "openai":
            try:
                from aicmo.llm.client import _get_openai_client
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    logger.debug("OPENAI_API_KEY not set, LLM provider unavailable")
                    return None
                
                client = _get_openai_client()
                
                def openai_provider(prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
                    """OpenAI GPT-4o-mini provider."""
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            max_tokens=max_tokens,
                            temperature=temperature,
                            messages=[{"role": "user", "content": prompt}],
                        )
                        if response.choices and len(response.choices) > 0:
                            return response.choices[0].message.content or ""
                        return ""
                    except Exception as e:
                        logger.debug(f"OpenAI LLM error: {e}")
                        return ""
                
                logger.debug("OpenAI GPT-4o-mini provider initialized")
                return openai_provider
                
            except ImportError:
                logger.debug("OpenAI SDK not installed, LLM provider unavailable")
                return None
        
        logger.debug(f"Unknown LLM provider: {provider_name}")
        return None
        
    except Exception as e:
        logger.debug(f"Failed to initialize LLM provider: {e}")
        return None
