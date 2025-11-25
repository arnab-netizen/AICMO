"""
Shared Helper Module for All Report Generators

This module provides:
- BrandBrief: unified data model ensuring all generators have required fields
- Sanitization functions: strip placeholders, replace generic tokens
- Validation: ensure required fields before generation
- Quality checks: detect and skip noise/error text

Use these helpers in every generator to ensure client-ready, placeholder-free output.
"""

import re
from typing import Iterable, List, Dict, Optional
from pydantic import BaseModel, Field


class BrandBrief(BaseModel):
    """
    Unified brand brief model used by all generators.

    **CRITICAL FIELDS:**
    - brand_name: Required for any personalization
    - industry: Required for context-aware generation
    - primary_customer: Required for audience-specific messaging
    - product_service: **REQUIRED** to fix 'no attribute product_service' errors

    Optional fields can be None but should NOT default to generic tokens.
    """

    brand_name: str = Field(..., description="Brand/company name")
    industry: str = Field(..., description="Industry category")
    primary_goal: str = Field(..., description="Primary marketing objective")
    timeline: str = Field(..., description="Campaign/planning timeline")
    primary_customer: str = Field(..., description="Main customer/audience segment")

    # Optional but recommended
    secondary_customer: Optional[str] = Field(None, description="Secondary audience segment")
    brand_tone: Optional[str] = Field(None, description="Brand voice/tone preferences")
    product_service: Optional[str] = Field(None, description="Product or service description")
    location: Optional[str] = Field(None, description="Geographic focus")

    # Collections
    competitors: List[str] = Field(default_factory=list, description="Competitor names")

    class Config:
        """Allow extra fields for backward compatibility."""

        extra = "allow"


# ============================================================================
# PLACEHOLDER & TOKEN DEFINITIONS
# ============================================================================

PLACEHOLDER_PATTERNS = [
    r"\[[^\]]*not yet implemented[^\]]*\]",
    r"\[insert [^\]]+\]",
    r"\[Brand Name\]",
    r"\[Founder Name\]",
    r"\[.*? - not yet implemented\]",
    r"\[.*?market.*?landscape.*?\]",
    r"\[.*?ad.*?concepts.*?\]",
]

GENERIC_TOKENS = [
    "your industry",
    "your category",
    "your audience",
    "your market",
    "your customers",
    "your solution",
    "{brand_name}",
    "{industry}",
    "{product_service}",
    "{primary_customer}",
]

ERROR_INDICATORS = [
    "not yet implemented",
    "error generating",
    "object has no attribute",
    "attribute error",
    "unexpected error",
    "traceback",
]


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================


def ensure_required_fields(
    brief: BrandBrief,
    required: Iterable[str],
) -> None:
    """
    Hard validation: ensure all required fields are present and non-empty.

    Args:
        brief: BrandBrief instance to validate
        required: Field names that MUST be present

    Raises:
        ValueError: With clear message listing missing fields

    Example:
        ensure_required_fields(brief, required=["brand_name", "industry", "primary_customer"])
    """
    missing = []
    for field in required:
        value = getattr(brief, field, None)
        if value in (None, "", []):
            missing.append(field)

    if missing:
        raise ValueError(
            f"Missing required brief fields for generation: {', '.join(missing)}. "
            f"Please populate these fields before generating content."
        )


# ============================================================================
# TOKEN REPLACEMENT & SANITIZATION
# ============================================================================


def apply_token_replacements(text: str, brief: BrandBrief) -> str:
    """
    Replace generic tokens ('your industry', 'your audience', etc.)
    with concrete values from the brief.

    This prevents generic fallbacks from leaking into the final output.

    Args:
        text: Raw generated text
        brief: BrandBrief with concrete values

    Returns:
        Text with all tokens replaced
    """
    replacements: Dict[str, str] = {
        "your industry": brief.industry or "the market",
        "your category": brief.industry or "the category",
        "your audience": brief.primary_customer or "your target audience",
        "your market": brief.industry or "your market",
        "your customers": brief.primary_customer or "your customers",
        "your solution": brief.product_service or brief.industry,
        "{brand_name}": brief.brand_name or "",
        "{industry}": brief.industry or "",
        "{product_service}": brief.product_service or "",
        "{primary_customer}": brief.primary_customer or "",
    }

    for token, replacement in replacements.items():
        text = text.replace(token, replacement)

    return text


def strip_placeholders(text: str) -> str:
    """
    Remove bracketed placeholder text and collapse excess whitespace.

    This aggressively removes:
    - [insert ...], [not yet implemented], [Brand Name], etc.
    - Excessive blank lines (3+ → 2)
    - Multiple spaces

    Args:
        text: Raw text with potential placeholders

    Returns:
        Cleaned text with placeholders removed
    """
    # Remove bracketed patterns
    for pattern in PLACEHOLDER_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Collapse multiple spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse multiple blank lines (3+ → 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def remove_error_text(text: str) -> str:
    """
    Remove lines containing error indicators or stack traces.

    This prevents "Error generating...", attribute errors, etc. from leaking.

    Args:
        text: Text that may contain error messages

    Returns:
        Text with error lines removed
    """
    lines = text.split("\n")
    clean_lines = []

    for line in lines:
        lowered = line.lower()
        # Skip lines that contain error indicators
        if any(indicator in lowered for indicator in ERROR_INDICATORS):
            continue
        # Skip lines that are obviously stack traces (start with spaces + "File" or similar)
        if re.match(r"^\s+(File|Traceback|at |>>>)", line):
            continue
        clean_lines.append(line)

    return "\n".join(clean_lines)


def sanitize_output(text: str, brief: BrandBrief) -> str:
    """
    Final sanitization step for ANY generator output.

    This is the last filter before returning text to aggregator.

    Steps:
    1. Replace generic tokens with brief values
    2. Strip bracketed placeholders
    3. Remove error text
    4. Collapse whitespace

    Args:
        text: Raw generator output
        brief: BrandBrief for token replacement

    Returns:
        Clean, client-ready text

    Example:
        raw = llm_client.generate(prompt)
        clean = sanitize_output(raw, brief)
        return clean
    """
    # Step 1: Replace tokens
    text = apply_token_replacements(text, brief)

    # Step 2: Strip placeholder brackets
    text = strip_placeholders(text)

    # Step 3: Remove error text
    text = remove_error_text(text)

    # Step 4: Final whitespace cleanup
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================================
# QUALITY & NOISE DETECTION
# ============================================================================


def is_empty_or_noise(text: str) -> bool:
    """
    Decide if a section is too noisy/short to include in the final report.

    Returns True (should be skipped) if:
    - Empty or None
    - Contains "not yet implemented"
    - Contains "error generating", "attribute error", etc.
    - Too short (<150 chars) after stripping

    Args:
        text: Section text to evaluate

    Returns:
        True if section should be skipped, False if it's usable
    """
    if not text or not isinstance(text, str):
        return True

    text = text.strip()

    if not text:
        return True

    lowered = text.lower()

    # Check for error indicators
    for indicator in ERROR_INDICATORS:
        if indicator in lowered:
            return True

    # Check for placeholder text
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    # Too short = likely incomplete
    if len(text) < 150:
        return True

    return False


def has_generic_tokens(text: str) -> bool:
    """
    Check if text still contains generic tokens that should have been replaced.

    Useful for debugging: if True, sanitize_output may have failed.

    Args:
        text: Text to check

    Returns:
        True if generic tokens are present
    """
    if not text:
        return False

    lowered = text.lower()
    return any(token.lower() in lowered for token in GENERIC_TOKENS)


# ============================================================================
# BLOCK-LEVEL FILTERING (FOR LEARNING)
# ============================================================================


def should_learn_block(text: str, min_length: int = 300) -> bool:
    """
    Filter whether a text block is suitable for the learning system.

    Returns False (skip) if:
    - Too short (<min_length chars)
    - Contains generic tokens or placeholders
    - Contains error text

    Args:
        text: Block text (e.g., a section from a report)
        min_length: Minimum character length to be considered valuable

    Returns:
        True if block is clean and valuable, False if it should be skipped
    """
    if not text or not isinstance(text, str):
        return False

    text = text.strip()

    # Check length
    if len(text) < min_length:
        return False

    lowered = text.lower()

    # Check for error indicators
    if any(indicator in lowered for indicator in ERROR_INDICATORS):
        return False

    # Check for placeholder patterns
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in PLACEHOLDER_PATTERNS):
        return False

    # Check for generic tokens
    if any(token.lower() in lowered for token in GENERIC_TOKENS):
        return False

    return True
