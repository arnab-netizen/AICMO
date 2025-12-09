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
    
    Args:
        pack_key: Pack identifier for logging
        section_id: Section identifier
        content: Current section text
        warnings: List of warnings from Layer 3 soft validators
        context: Context dict with brand, campaign, market data
        req: GenerateRequest object
        llm_provider: Optional LLM provider callable (sync or async)
    
    Returns:
        Rewritten section text (str), or original content if rewrite fails/skipped
        
    Guarantees:
        - Never raises HTTPException
        - Never blocks user
        - Always returns string (original content on any error)
        - Max 1 rewrite attempt
        - Preserves structure and headings
    """
    try:
        # If no LLM provider, can't rewrite
        if llm_provider is None:
            logger.debug(f"No LLM provider, skipping rewrite for {section_id}")
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
        
        rewrite_prompt = f"""You are a senior marketing copywriter. Rewrite this section to improve quality.

Section: {section_id}
Brand: {brand_name}
Campaign: {campaign_name}
Target Audience: {target_audience}

Issues to fix:
{issue_summary}

Rewrite guidelines:
1. Make the content more specific and less generic
2. Eliminate clichés (avoid "boost your brand", "in today's world", "unlock potential", etc.)
3. Add concrete details, examples, or numbers where appropriate
4. Ensure proper structure and formatting is preserved
5. Improve hooks and CTAs to be more compelling
6. Keep word count within 20% of original (original: ~{len(content.split())} words)

Original section:
{content}

Rewritten section (improve quality while preserving structure):"""

        # Call LLM for rewrite
        try:
            rewritten = llm_provider(
                prompt=rewrite_prompt,
                max_tokens=min(2500, len(content.split()) * 2 + 300),
                temperature=0.8,
            )
            
            # Handle case where result is a coroutine (async)
            import inspect
            if inspect.iscoroutine(rewritten):
                logger.debug("LLM provider returned coroutine, cannot await from sync context")
                return content
            
        except Exception as e:
            logger.debug(f"LLM call exception: {e}")
            return content
        
        if not rewritten or not isinstance(rewritten, str) or not rewritten.strip():
            logger.debug(f"Rewriter returned empty result for {section_id}")
            return content
        
        logger.warning(
            f"Section rewritten",
            extra={
                "pack_key": pack_key,
                "section_id": section_id,
                "issues": warnings,
            },
        )
        return rewritten
        
    except Exception as e:
        logger.error(
            f"Rewriter failed for {section_id}, returning original content",
            extra={"error": str(e)},
            exc_info=True,
        )
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
