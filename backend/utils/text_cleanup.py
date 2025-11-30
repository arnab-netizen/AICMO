"""
Text Cleanup Utilities for AICMO

Provides cleaning and normalization functions for Quick Social and other packs.
Removes template leaks, banned phrases, and improves content quality.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.main import GenerateRequest


def normalize_hashtag(tag: str) -> str:
    """
    Normalize a hashtag to valid format.

    Rules:
    - Lowercase
    - Remove slashes and spaces
    - Keep only letters, digits, underscores
    - Prepend # if missing

    Args:
        tag: Raw hashtag string (may contain invalid characters)

    Returns:
        Normalized hashtag (e.g., "#coffeehouse") or empty string if invalid

    Examples:
        >>> normalize_hashtag("Coffeehouse / Beverage Retail")
        '#coffeehousebeverageretail'
        >>> normalize_hashtag("#Coffee Shop")
        '#coffeeshop'
        >>> normalize_hashtag("coffee-lover")
        '#coffeelover'
    """
    # Lower and strip
    tag = tag.strip().lower()

    # Remove slashes and spaces
    tag = tag.replace("/", "").replace(" ", "")

    # Keep only letters, digits, underscore
    tag = re.sub(r"[^a-z0-9_]", "", tag)

    if not tag:
        return ""

    # Prepend # if missing
    if not tag.startswith("#"):
        tag = "#" + tag

    return tag


def clean_quick_social_text(text: str, req: GenerateRequest) -> str:
    """
    Apply Quick Social-specific language hygiene rules.

    Removes:
    - Template placeholders ("ideal customers", "over the next period")
    - Repetitive goal sentences
    - Duplicate brand taglines
    - Punctuation issues (double periods, ", .")

    Args:
        text: Raw section text
        req: GenerateRequest with brand brief

    Returns:
        Cleaned text with template leaks removed

    Example:
        >>> clean_quick_social_text("We target ideal customers...", req)
        'We target busy professionals...'  # Assuming persona_name set
    """
    brand_name = (req.brief.brand.brand_name or "your brand").strip()

    # 1) Replace literal 'ideal customers'
    persona_name = getattr(req.brief.audience, "primary_customer", "").strip()
    if persona_name:
        text = text.replace("ideal customers", persona_name)
        text = text.replace("ideal customer", persona_name)
    else:
        text = text.replace("ideal customers", "your target customers")
        text = text.replace("ideal customer", "your target customer")

    # 2) Remove generic template phrases
    BANNED_PHRASES = [
        "over the next period",
        "within the near term timeframe",
        "Key considerations include the audience's core pain points",
        "in today's digital age",  # Already in benchmarks but extra safety
        "content is king",
    ]
    for phrase in BANNED_PHRASES:
        text = text.replace(phrase, "")

    # 3) Avoid repeating the full objective sentence multiple times
    if req.brief.goal.primary_goal:
        goal = req.brief.goal.primary_goal.strip()
        full_goal_sentence = f"{brand_name} is aiming to drive {goal}."
        # Allow only once
        first_index = text.find(full_goal_sentence)
        if first_index != -1:
            # Strip subsequent duplicates
            before_first = text[: first_index + len(full_goal_sentence)]
            after_first = text[first_index + len(full_goal_sentence) :]
            after_first = after_first.replace(full_goal_sentence, "This goal.")
            text = before_first + after_first

    # 4) Throttle 'We replace random acts of marketing' to at most once
    MAX_PHRASE = "We replace random acts of marketing with a simple, repeatable system."
    occurrences = text.count(MAX_PHRASE)
    if occurrences > 1:
        # Keep first, delete rest
        first = text.find(MAX_PHRASE)
        before = text[: first + len(MAX_PHRASE)]
        after = text[first + len(MAX_PHRASE) :].replace(MAX_PHRASE, "")
        text = before + after

    # 5) Fix double periods and stray commas
    while ".." in text:
        text = text.replace("..", ".")
    text = text.replace(", .", ".").replace(",  .", ".")

    # 6) Clean up excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)  # Max 2 newlines
    text = re.sub(r" {2,}", " ", text)  # Max 1 space

    return text.strip()
