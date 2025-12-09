"""
Context Sanitization & Text Cleanup Utilities

Fixes for placeholders, number normalization, typos, synonym rotation, and tone control.
"""

import re
from typing import Any, Optional


# ═══════════════════════════════════════════════════════════════════════
# FIX #1: CONTEXT SANITIZATION (Placeholders)
# ═══════════════════════════════════════════════════════════════════════

PLACEHOLDER_STRINGS = {
    "not_specified": {"not specified", "none", "-", "n/a", "unknown", "tbd"},
    "empty_like": {"", " ", "  ", "   "},
}


def _is_unspecified(value: str) -> bool:
    """Check if value is a placeholder or empty-like string."""
    if not value:
        return True
    v = value.strip().lower()
    return v in PLACEHOLDER_STRINGS["not_specified"] or v in PLACEHOLDER_STRINGS["empty_like"]


def sanitize_brief_context(ctx: Any) -> Any:
    """
    Ensure we never leak raw placeholders like 'your target audience',
    'Not specified', or empty strings into the prompts.

    Replaces unspecified brief fields with neutral, human-sounding fallbacks.
    Handles both top-level attributes and nested objects (brief.brand.industry, etc.)

    Args:
        ctx: Context object (e.g., ClientInputBrief, GenerateRequest, or dict-like)

    Returns:
        The same ctx object with sanitized fields
    """
    # Top-level attribute sanitization
    fallback_map = {
        "primary_customer": "the intended customer segment",
        "secondary_customer": "additional audiences relevant to the brand",
        "industry": "the relevant industry",
        "primary_goal": "the brand's main objective",
        "timeline": "the next 30 to 90 days",
        "brand_adjectives": "professional, trustworthy, and reliable",
        "brand_name": "the brand",
        "founder_name": None,  # Special handling: if None, don't use
    }

    for attr, fallback in fallback_map.items():
        if not hasattr(ctx, attr):
            continue

        try:
            value = getattr(ctx, attr)
        except Exception:
            continue

        # If value is unspecified, replace with fallback
        if value is None and fallback:
            setattr(ctx, attr, fallback)
        elif isinstance(value, str) and _is_unspecified(value):
            if fallback:
                setattr(ctx, attr, fallback)
            else:
                setattr(ctx, attr, "")

    # Nested object sanitization (for brief.brand.industry, brief.audience.primary_customer, etc.)
    nested_fallback_map = {
        ("brand", "industry"): "the relevant industry",
        ("brand", "primary_goal"): "the brand's main objective",
        ("brand", "product_service"): "your main product or service",
        ("brand", "primary_customer"): "the intended customer segment",
        ("audience", "primary_customer"): "the intended customer segment",
        ("goal", "primary_goal"): "the brand's main objective",
    }
    
    for (obj_name, attr_name), fallback in nested_fallback_map.items():
        if not hasattr(ctx, obj_name):
            continue
        
        try:
            obj = getattr(ctx, obj_name)
            if not hasattr(obj, attr_name):
                continue
            
            value = getattr(obj, attr_name)
            
            # If value is unspecified, replace with fallback
            if value is None and fallback:
                setattr(obj, attr_name, fallback)
            elif isinstance(value, str) and _is_unspecified(value):
                if fallback:
                    setattr(obj, attr_name, fallback)
                else:
                    setattr(obj, attr_name, "")
        except Exception:
            continue

    return ctx


# ═══════════════════════════════════════════════════════════════════════
# FIX #2: SYNONYM ROTATION & BORING TONE
# ═══════════════════════════════════════════════════════════════════════


def _apply_synonym_rotation(content: str, brand_name: Optional[str] = None) -> str:
    """
    Reduce over-use of the brand name and generic 'test' tokens.
    Keep output readable, conservative, and "boring professional".

    Args:
        content: Text to process
        brand_name: Brand name to rotate out (optional)

    Returns:
        Content with synonym rotation applied
    """
    if not content:
        return content

    # Only rotate brand name if it's reasonable (not "test" or empty)
    if brand_name and brand_name.lower() not in {"test", "testbrand", ""}:
        # Count occurrences to decide if rotation is needed
        brand_count = content.lower().count(brand_name.lower())

        # Only apply if brand name appears more than 3 times
        if brand_count > 3:
            # First occurrence: keep it; subsequent: use "the brand"
            parts = content.split(brand_name)
            result = parts[0] + brand_name
            for i, part in enumerate(parts[1:], 1):
                # Every other occurrence (to not remove all)
                if i % 2 == 0:
                    result += brand_name + part
                else:
                    result += "the brand" + part
            content = result

    return content


# ═══════════════════════════════════════════════════════════════════════
# FIX #3: NUMBER NORMALIZATION
# ═══════════════════════════════════════════════════════════════════════


def normalize_numbers(content: str) -> str:
    """
    Fix broken numbers like 20,00 -> 20,000; 5,00 -> 5,000, etc.
    Conservative pass - only fix known bad patterns.

    Args:
        content: Text to process

    Returns:
        Content with normalized numbers
    """
    if not content:
        return content

    text = content

    # Direct replacement for common broken patterns
    replacements = {
        "20,00": "20,000",
        "40,00": "40,000",
        "65,00": "65,000",
        "5,00": "5,000",
        "10,00": "10,000",
        "1,00": "1,000",
        "2,00": "2,000",
        "3,00": "3,000",
    }

    for bad, good in replacements.items():
        text = text.replace(bad, good)

    # Range patterns like "5,00–10,00" -> "5,000–10,000"
    text = re.sub(r"(\d{1,2}),00–(\d{1,2}),00", r"\g<1>,000–\g<2>,000", text)
    text = re.sub(r"(\d{1,2}),00-(\d{1,2}),00", r"\g<1>,000-\g<2>,000", text)

    return text


# ═══════════════════════════════════════════════════════════════════════
# FIX #5: GRAMMAR & SPELLCHECK PASS
# ═══════════════════════════════════════════════════════════════════════


def basic_typos_cleanup(content: str) -> str:
    """
    Fix common obvious typos without being too aggressive.
    Conservative word-boundary checks to avoid changing code/URLs.

    Args:
        content: Text to process

    Returns:
        Content with obvious typos fixed
    """
    if not content:
        return content

    text = content

    # Word-boundary typo fixes (conservative)
    replacements = [
        (r"\bse\s", "see "),
        (r"\bSe\s", "See "),
        (r"\bfre\s", "free "),
        (r"\bFre\s", "Free "),
        (r"\bles\s", "less "),
        (r"\bLes\s", "Less "),
        (r"\bcros-sell", "cross-sell"),
        (r"\bCros-sell", "Cross-sell"),
        (r"\bopennes", "openness"),
        (r"\bOpenness", "Openness"),
        (r"\bbusines\b", "business"),
        (r"\bBusines\b", "Business"),
        (r"\bimmediate\s+effect", "immediate effect"),
    ]

    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text


# ═══════════════════════════════════════════════════════════════════════
# FIX #7: FOUNDER NAME PLACEHOLDER
# ═══════════════════════════════════════════════════════════════════════


def remove_founder_placeholder_if_missing(content: str, founder_name: Optional[str]) -> str:
    """
    Remove [Founder's Name] placeholder if founder_name is missing.
    Adjust narrative to brand-level story if name unavailable.

    Args:
        content: Text to process
        founder_name: Founder's actual name (or None/empty)

    Returns:
        Content with founder placeholder handled appropriately
    """
    if not content:
        return content

    if founder_name and founder_name.lower() not in {"", "not specified", "unknown"}:
        # Founder name is present; replace placeholder if any
        content = re.sub(r"\[Founder'?s?\s+Name\]", founder_name, content, flags=re.IGNORECASE)
    else:
        # Founder name missing; remove placeholder lines
        lines = content.split("\n")
        filtered = []
        for line in lines:
            # Skip lines that are ONLY the placeholder
            if "[Founder" not in line or (len(line.strip()) > 50):
                filtered.append(line)
        content = "\n".join(filtered)

        # Also remove inline placeholders
        content = re.sub(r"\s*\[Founder'?s?\s+Name\]\s*", " the founder ", content, flags=re.IGNORECASE)

    return content


# ═══════════════════════════════════════════════════════════════════════
# FIX #1 (Content Level): Clean up placeholder text in content
# ═══════════════════════════════════════════════════════════════════════


def _cleanup_content_placeholders(content: str) -> str:
    """
    Remove or replace placeholder text that may appear in generated content.
    Handles phrases like "your target audience", "your main objective", etc.
    
    Args:
        content: Text to process
    
    Returns:
        Content with placeholder phrases replaced
    """
    if not content:
        return content
    
    # Placeholder phrases to replace with neutral alternatives
    replacements = {
        r"your target audience": "the intended audience",
        r"your main objective": "the primary objective",
        r"your primary goal": "the main goal",
        r"your industry": "the relevant industry",
        r"your main product": "the primary product",
        r"your main product/service": "the main offering",
        r"your brand": "the brand",
        r"your business": "the business",
        r"your market": "the market",
        r"your customers": "customers",
        r"your audience": "the audience",
        r"your goal": "the goal",
        r"your objective": "the objective",
        r"your offering": "the offering",
    }
    
    text = content
    for pattern, replacement in replacements.items():
        # Case-insensitive replacement at word boundaries
        text = re.sub(r'\b' + pattern + r'\b', replacement, text, flags=re.IGNORECASE)
    
    return text


# ═══════════════════════════════════════════════════════════════════════
# COMPOSITE: Apply all non-LLM fixes at once
# ═══════════════════════════════════════════════════════════════════════


def apply_all_cleanup_passes(
    content: str,
    brand_name: Optional[str] = None,
    founder_name: Optional[str] = None,
) -> str:
    """
    Apply all non-LLM text cleanup passes in sequence.
    Conservative, predictable, "boring" output.

    Args:
        content: Text to process
        brand_name: Optional brand name for synonym rotation
        founder_name: Optional founder name

    Returns:
        Cleaned-up content
    """
    if not content:
        return content

    # Order matters: content placeholders first, then numbers, then typos, then founder, then synonyms
    content = _cleanup_content_placeholders(content)
    content = normalize_numbers(content)
    content = basic_typos_cleanup(content)
    content = remove_founder_placeholder_if_missing(content, founder_name)
    content = _apply_synonym_rotation(content, brand_name)

    return content
