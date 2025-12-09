"""
LAYER 3: SOFT VALIDATORS (NON-BLOCKING)

Purpose: Score and flag issues without blocking.

Returns:
  (text, quality_score, genericity_score, warnings)
  
  - quality_score (0-100): Based on structure, length, placeholders
  - genericity_score (0-100): 0=very generic, 100=very specific
  - warnings (list): e.g., ["missing_cta", "too_generic_hooks", "too_short"]

Key: Never raises HTTPException. All errors logged internally.

Quality Score Ranges (used by Layer 4):
  - quality_score >= 80 → OK, no rewrite
  - 60 ≤ quality_score < 80 → Warnings only, no auto-rewrite
  - quality_score < 60 → Trigger ONE section-level rewrite

Logging:
  - WARNING: quality_score < 80
  - DEBUG: validator details, exact patterns, etc.
"""

import logging
import re
from typing import Tuple, List, Optional

logger = logging.getLogger(__name__)

# Clichés and generic phrases (case-insensitive)
# These are soft signals that reduce quality_score
GENERIC_PHRASES = [
    r"boost your brand",
    r"grow your business",
    r"take your business to the next level",
    r"unlock your potential",
    r"in today's digital world",
    r"in today's fast-paced world",
    r"drive more engagement",
    r"results-driven strategy",
    r"cutting-edge solutions",
    r"maximize your reach",
    r"elevate your presence",
    r"seamless integration",
    r"best-in-class",
    r"game-changer",
    r"revolutionary approach",
    r"breakthrough innovation",
    r"synergize your efforts",
    r"leverage your assets",
    r"optimized performance",
    r"data-driven insights",
]

# Placeholder patterns
PLACEHOLDER_PATTERNS = [
    r"\[.*?\]",  # [text]
    r"\{.*?\}",  # {text}
    r"\btbd\b",
    r"\bn/a\b",
    r"\binsert\b",
    r"\bfill in\b",
    r"\bcustomer name\b",
    r"\bbrand name\b",
    r"\bcampaign name\b",
    r"\byour.*?\b",
    r"\bour.*?\b",  # vague
    r"\bxxx\b",
    r"\b\d+\s*xxx\b",
]


def _compile_patterns(patterns: List[str]) -> List[re.Pattern]:
    """Compile regex patterns once for efficiency."""
    return [re.compile(p, re.IGNORECASE) for p in patterns]


GENERIC_PATTERNS = _compile_patterns(GENERIC_PHRASES)
PLACEHOLDER_PATTERNS_COMPILED = _compile_patterns(PLACEHOLDER_PATTERNS)


def _check_structural_integrity(text: str, section_id: str) -> Tuple[bool, List[str]]:
    """
    Validate that required structural elements are present.
    
    Returns:
        (is_valid, warnings)
    """
    warnings = []
    
    # Sections should have minimum length
    if not text or len(text.strip()) < 50:
        warnings.append("too_short")
    
    # Check for common required elements based on section type
    if section_id in ["overview", "executive_summary", "strategy"]:
        if "goal" not in text.lower() and "objective" not in text.lower():
            warnings.append("missing_goals_or_objectives")
    
    if "cta" not in text.lower() and "call to action" not in text.lower() and "contact" not in text.lower():
        if section_id in ["overview", "campaign_objective", "creatives_headline"]:
            warnings.append("missing_cta")
    
    return len(warnings) == 0, warnings


def _check_placeholders(text: str) -> Tuple[int, List[str]]:
    """
    Count and identify placeholder patterns.
    
    Returns:
        (count, warnings)
    """
    count = 0
    warnings = []
    
    for pattern in PLACEHOLDER_PATTERNS_COMPILED:
        matches = pattern.findall(text)
        if matches:
            count += len(matches)
            logger.debug(f"Found {len(matches)} placeholder matches: {matches[:3]}")
    
    if count > 0:
        warnings.append("has_placeholders")
    
    return count, warnings


def _check_genericity(text: str) -> Tuple[int, List[str]]:
    """
    Check for clichés and generic phrases.
    
    Returns:
        (generic_phrase_count, warnings)
    """
    count = 0
    warnings = []
    found_phrases = []
    
    for pattern in GENERIC_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            count += len(matches)
            found_phrases.extend(matches[:2])  # Log first 2 matches
    
    if count >= 3:
        warnings.append("too_many_cliches")
        logger.debug(f"Found {count} generic phrases: {found_phrases}")
    elif count >= 1:
        warnings.append("has_some_cliches")
    
    return count, warnings


def _check_length_bounds(text: str, section_id: str) -> Tuple[bool, List[str]]:
    """
    Check if text length is within reasonable bounds.
    
    Returns:
        (is_good, warnings)
    """
    warnings = []
    word_count = len(text.split())
    
    # Expected word counts by section type
    expected_ranges = {
        "overview": (150, 400),
        "campaign_objective": (100, 250),
        "creatives_headline": (50, 150),
        "strategy": (200, 500),
        "social_calendar": (500, 2000),
        "media_plan": (100, 300),
    }
    
    if section_id in expected_ranges:
        min_words, max_words = expected_ranges[section_id]
        if word_count < min_words:
            warnings.append("too_short")
        elif word_count > max_words:
            warnings.append("too_long")
    
    return len(warnings) == 0, warnings


def run_soft_validators(
    pack_key: str,
    section_id: str,
    content: str,
    context: dict,
) -> Tuple[str, Optional[int], Optional[int], List[str]]:
    """
    Score and flag issues without blocking.
    
    Args:
        pack_key: Pack identifier for logging
        section_id: Section identifier
        content: Section text to validate
        context: Context dict with brand, campaign data
    
    Returns:
        (content, quality_score, genericity_score, warnings)
        
        - quality_score (0-100): 0=very poor, 100=excellent
        - genericity_score (0-100): 0=very generic, 100=very specific
        - warnings (list): detected issues
    
    Guarantees:
        - Never raises HTTPException
        - Never blocks user
        - Returns tuple even if validation fails
    """
    try:
        warnings = []
        quality_score = 100
        genericity_score = 100
        
        # 1. Check structural integrity
        struct_ok, struct_warnings = _check_structural_integrity(content, section_id)
        warnings.extend(struct_warnings)
        if not struct_ok:
            quality_score -= 20
        
        # 2. Check placeholders
        placeholder_count, placeholder_warnings = _check_placeholders(content)
        warnings.extend(placeholder_warnings)
        quality_score -= min(30, placeholder_count * 10)  # Up to 30 points
        
        # 3. Check genericity (clichés)
        generic_count, generic_warnings = _check_genericity(content)
        warnings.extend(generic_warnings)
        # Genericity impacts both scores
        genericity_reduction = min(40, generic_count * 15)
        genericity_score -= genericity_reduction
        quality_score -= genericity_reduction // 2
        
        # 4. Check length bounds
        length_ok, length_warnings = _check_length_bounds(content, section_id)
        warnings.extend(length_warnings)
        if not length_ok:
            quality_score -= 10
        
        # Clamp scores
        quality_score = max(0, min(100, quality_score))
        genericity_score = max(0, min(100, genericity_score))
        
        # Log based on quality
        if quality_score >= 80:
            logger.debug(
                f"Soft validator OK for {section_id}",
                extra={
                    "pack_key": pack_key,
                    "quality_score": quality_score,
                    "genericity_score": genericity_score,
                },
            )
        else:
            logger.warning(
                f"Low quality section detected",
                extra={
                    "pack_key": pack_key,
                    "section_id": section_id,
                    "quality_score": quality_score,
                    "genericity_score": genericity_score,
                    "warnings": warnings,
                },
            )
        
        return content, quality_score, genericity_score, warnings
        
    except Exception as e:
        logger.error(
            f"Unexpected error in soft validators",
            extra={"section_id": section_id, "error": str(e)},
            exc_info=True,
        )
        # Return content as-is with neutral scores on error
        return content, 50, 50, ["validation_error"]
