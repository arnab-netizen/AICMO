"""
LAYER 4: SECTION-LEVEL REWRITER (OPTIONAL, NON-BLOCKING)

Purpose: Improve weak sections without blocking.

Triggered when: quality_score < 60

Behavior:
- Max 1 rewrite attempt per section
- Preserves structure and headings
- On ANY error → silently returns previous version (no exception)

Key: This layer NEVER raises HTTPException or blocks. Always returns string.

Quality Thresholds:
  - quality_score >= 80 → No rewrite, just log "OK"
  - 60 ≤ quality_score < 80 → Warnings only, no auto-rewrite
  - quality_score < 60 → Trigger ONE section-level rewrite
"""

import logging
from typing import Optional, List, Callable

from backend.layers.utils_context import apply_all_cleanup_passes

logger = logging.getLogger(__name__)

# Threshold for triggering rewrites
REWRITE_THRESHOLD = 60


def rewrite_low_quality_section(
    pack_key: str,
    section_id: str,
    content: str,
    warnings: List[str],
    context: dict,
    req,
    llm_provider: Optional[Callable] = None,
) -> str:
    """
    Rewrite weak section for improved quality (SYNCHRONOUS).
    
    Triggered when: quality_score < 60 (from Layer 3 soft validators)
    
    Behavior:
    1. If no LLM provider, try to get one from factory
    2. If still no provider, return original content
    3. Build rewrite prompt addressing specific issues
    4. Call LLM once (max 1 rewrite attempt per section)
    5. On ANY error, return original content (never raise)
    
    Args:
        pack_key: Pack identifier for logging
        section_id: Section identifier (e.g., "overview", "strategy")
        content: Current section text from Layer 3
        warnings: List of warnings from Layer 3 soft validators
        context: Context dict with brand, campaign, market data
        req: GenerateRequest object
        llm_provider: Optional LLM provider callable (will use factory if None)
    
    Returns:
        Rewritten section text (str), or original content if rewrite fails/skipped
        
    Guarantees:
        - Never raises HTTPException
        - Never blocks user
        - Always returns string (original content on any error)
        - Max 1 rewrite attempt per section
        - Preserves structure and headings
    """
    try:
        # If no LLM provider injected, try to get one from factory
        if llm_provider is None:
            from backend.layers import get_llm_provider
            llm_provider = get_llm_provider()
        
        # If still no LLM provider, can't rewrite
        if llm_provider is None:
            logger.debug(f"No LLM provider available, skipping rewrite for {section_id}")
            return content
        
        # If content is empty, nothing to rewrite
        if not content or not content.strip():
            logger.debug(f"Empty content for {section_id}, skipping rewrite")
            return content
        
        # Build rewrite prompt
        brand_name = context.get("brand_name", "")
        campaign_name = context.get("campaign_name", "")
        target_audience = context.get("target_audience", "")
        
        # Explain what's weak
        issue_summary = _summarize_issues(warnings)
        word_count = len(content.split())
        
        rewrite_prompt = f"""You are a senior marketing copywriter. Rewrite this section to improve quality and address specific issues.

[SECTION]: {section_id}
[BRAND]: {brand_name}
[CAMPAIGN]: {campaign_name}
[TARGET AUDIENCE]: {target_audience}

[ISSUES TO FIX]:
{issue_summary}

[REWRITE GUIDELINES]:
1. Make content more specific and less generic/clichéd
2. Eliminate: "boost your brand", "in today's world", "unlock potential", "best-in-class", "game-changer", "synergize"
3. Add concrete details: examples, numbers, case studies, data points
4. Improve CTAs and hooks to be compelling and action-oriented
5. PRESERVE all structure, headings, and formatting exactly as in original
6. Keep word count ±20% of original ({word_count} words) – target: {int(word_count * 0.9)}-{int(word_count * 1.1)} words

[ORIGINAL SECTION]:
{content}

[TASK]: Rewrite section to fix issues while preserving ALL structure and formatting. Output ONLY the rewritten section, no explanations."""

        # Call LLM for rewrite (max 1 attempt)
        try:
            rewritten = llm_provider(
                prompt=rewrite_prompt,
                max_tokens=min(2500, word_count * 2 + 400),
                temperature=0.8,
            )
            
            # Handle case where result is a coroutine (async)
            import asyncio
            if asyncio.iscoroutine(rewritten):
                logger.debug("LLM provider returned coroutine, cannot await from sync context")
                return content
            
        except Exception as e:
            logger.warning(f"LLM rewriter call failed for {section_id}: {type(e).__name__}: {e}")
            return content
        
        if not rewritten or not isinstance(rewritten, str) or not rewritten.strip():
            logger.debug(f"Rewriter returned empty result for {section_id}")
            return content
        
        # Verify rewritten text is substantial (at least 50% of original)
        if len(rewritten.strip()) < len(content.strip()) * 0.5:
            logger.debug(f"Rewritten text is too short for {section_id}, rejecting")
            return content
        
        logger.warning(
            f"Section rewritten (quality < 60)",
            extra={
                "pack_key": pack_key,
                "section_id": section_id,
                "issues_fixed": len(warnings),
                "size_change": f"{len(content)} → {len(rewritten)} chars",
            },
        )
        
        # Apply cleanup passes (even to rewritten content)
        brand_name = context.get("brand_name") if context else None
        founder_name = context.get("founder_name") if context else None
        rewritten = apply_all_cleanup_passes(rewritten, brand_name, founder_name)
        
        return rewritten
        
    except Exception as e:
        logger.warning(
            f"Unexpected error in rewriter for {section_id}: {type(e).__name__}: {e}"
        )
        content = apply_all_cleanup_passes(content, context.get("brand_name") if context else None, context.get("founder_name") if context else None)
        return content


def _summarize_issues(warnings: List[str]) -> str:
    """
    Convert warning list to human-readable issue summary.
    
    Args:
        warnings: List of warning codes
    
    Returns:
        Formatted issue summary
    """
    issue_map = {
        "too_short": "- Content is too short (needs more depth)",
        "too_long": "- Content is too long (needs trimming)",
        "missing_cta": "- Missing clear call to action",
        "missing_goals_or_objectives": "- Missing goals or objectives",
        "has_placeholders": "- Contains placeholder text like [brackets] or {braces}",
        "too_many_cliches": "- Too many generic/clichéd phrases",
        "has_some_cliches": "- Contains some generic/clichéd phrases",
        "validation_error": "- Validation issue (review content)",
    }
    
    issues = []
    for warning in warnings:
        if warning in issue_map:
            issues.append(issue_map[warning])
        else:
            issues.append(f"- {warning}")
    
    return "\n".join(issues) if issues else "- General quality improvement needed"
