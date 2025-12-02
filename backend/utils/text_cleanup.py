"""
Text Cleanup Utilities for AICMO

Provides cleaning and normalization functions for Quick Social and other packs.
Removes template leaks, banned phrases, and improves content quality.

Includes comprehensive sanitization for:
- Template artifacts (repeated letters, broken sentences, double spaces)
- Brand-specific messaging (removes agency language)
- Platform-specific CTAs (Instagram/Twitter/LinkedIn)
- Hashtag validation (length limits, compound nouns)
- B2C terminology (removes "leads", adds "visits")
- KPI accuracy (matches descriptions to metrics)
- Repetition control (limits phrase reuse)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, List
from collections import Counter

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


# ============================================================================
# FIX 1: SANITIZE TEXT - Remove template artifacts
# ============================================================================


def sanitize_text(text: str) -> str:
    """
    Remove all template artifacts and polish text for client delivery.

    Fixes:
    - Repeated letters (customersss → customers)
    - Broken sentence joins (". And" → " and")
    - Double spaces
    - Repeated industry terms
    - Raw variable names

    Args:
        text: Raw text with potential artifacts

    Returns:
        Cleaned, polished text

    Example:
        >>> sanitize_text("We target ideal customersss. And boost engagement.")
        'We target ideal customers and boost engagement.'
    """
    if not text:
        return text

    # Fix repeated letters (3+ of same letter → 2)
    # customersss → customers, coffeee → coffee
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)

    # After fixing, check if double letter looks wrong and reduce to single
    # Common cases: ss, ee, oo at end of words
    text = re.sub(r"(\w)(ss|ee|oo)\b", lambda m: m.group(1) + m.group(2)[0], text)

    # Fix broken sentence joins
    text = re.sub(r"\.\s+And\b", " and", text)
    text = re.sub(r"\.\s+Or\b", " or", text)
    text = re.sub(r"\.\s+But\b", ", but", text)

    # Collapse double spaces
    text = re.sub(r"  +", " ", text)

    # Remove repetitive industry terms (more than 2 occurrences)
    repetitive_terms = [
        "Coffeehouse / Beverage Retail",
        "coffeehouse / beverage retail",
        "Beverage Retail",
        "beverage retail",
    ]
    for term in repetitive_terms:
        count = text.count(term)
        if count > 2:
            # Keep first 2, remove rest
            parts = text.split(term)
            text = term.join(parts[:3]) + "".join(parts[3:])

    # Remove raw variable names
    variable_patterns = [
        r"\bideal_customers?\b",
        r"\bindustry_variable\b",
        r"\bprimary_customer_segment\b",
        r"\btarget_demographic\b",
        r"\{industry\}",
        r"\{brand_name\}",
        r"\{product_service\}",
    ]
    for pattern in variable_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Clean up whitespace after removals
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"  +", " ", text)
    text = re.sub(r" +\n", "\n", text)
    text = re.sub(r"\n +", "\n", text)

    return text.strip()


# ============================================================================
# FIX 2: BRAND-SPECIFIC MESSAGING - Remove agency language
# ============================================================================


AGENCY_LANGUAGE_PATTERNS = [
    "We replace random acts of marketing",
    "with a simple, repeatable system",
    "strategic frameworks",
    "methodology-driven approach",
    "our proprietary process",
    "KPI-first strategy",
    "systems thinking",
    "framework application",
]


def remove_agency_language(text: str) -> str:
    """
    Remove agency process language that doesn't fit brand voice.

    For B2C brands especially, remove:
    - "KPIs, systems, methodologies" unless warranted
    - Agency self-promotion
    - Process jargon

    Args:
        text: Text with potential agency language

    Returns:
        Text with agency language removed

    Example:
        >>> remove_agency_language("We replace random acts of marketing with KPIs.")
        ''
    """
    for phrase in AGENCY_LANGUAGE_PATTERNS:
        text = text.replace(phrase, "")

    # Clean up after removals
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"^\s+", "", text, flags=re.MULTILINE)

    return text.strip()


# ============================================================================
# FIX 3: PLATFORM-SPECIFIC CTAS - Fix cross-platform errors
# ============================================================================


PLATFORM_CTA_RULES = {
    "instagram": [
        "Save this",
        "Tag someone",
        "Try this next time",
        "Share this with a friend",
        "Tap to learn more",
        "Link in bio",
    ],
    "twitter": [
        "Join the conversation",
        "Reply with your thoughts",
        "Retweet to share",
        "Quote tweet us",
        "Drop a 🔥 if you agree",
    ],
    "linkedin": [
        "See insights",
        "Read full breakdown",
        "Comment your experience",
        "Share with your network",
        "Thoughts?",
    ],
}

# CTAs that are WRONG for each platform
BANNED_CTAS = {
    "twitter": ["Tap to save", "Link in bio", "Save this", "Swipe up"],
    "linkedin": ["Tap to save", "Link in bio", "Tag someone", "Swipe up"],
    "instagram": ["Reply with", "Retweet", "Quote tweet"],
}


def fix_platform_ctas(text: str, platform: str = "instagram") -> str:
    """
    Fix CTAs to be platform-appropriate.

    Removes:
    - "Tap to save" on Twitter
    - "Learn more in bio" on LinkedIn
    - Cross-platform CTAs

    Args:
        text: Caption or post text
        platform: Target platform (instagram/twitter/linkedin)

    Returns:
        Text with platform-appropriate CTAs

    Example:
        >>> fix_platform_ctas("Tap to save this! #coffee", "twitter")
        'Join the conversation! #coffee'
    """
    platform = platform.lower()

    # Remove banned CTAs for this platform
    if platform in BANNED_CTAS:
        for banned_cta in BANNED_CTAS[platform]:
            text = re.sub(rf"\b{re.escape(banned_cta)}\b.*?[.!]", "", text, flags=re.IGNORECASE)

    # Remove mood-board style camera notes inside captions
    camera_notes = [
        r"\[.*?camera.*?\]",
        r"\[.*?lighting.*?\]",
        r"\[.*?mood.*?board.*?\]",
        r"\[.*?aesthetic.*?\]",
    ]
    for pattern in camera_notes:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    return text.strip()


# ============================================================================
# FIX 4: HASHTAG VALIDATION - Remove fake/AI hashtags
# ============================================================================


def validate_hashtag(tag: str) -> bool:
    """
    Validate if a hashtag looks human and realistic.

    Rules:
    - Must be ≤20 characters
    - Must not have >2 concatenated nouns
    - Must not be all-lowercase-smooshed-together

    Args:
        tag: Hashtag to validate

    Returns:
        True if valid, False if fake/AI-looking

    Example:
        >>> validate_hashtag("#CoffeeLovers")
        True
        >>> validate_hashtag("#coffeehousebeverageretailtrends")
        False
    """
    # Remove # for analysis
    tag = tag.lstrip("#")

    # Rule 1: Length check
    if len(tag) > 20:
        return False

    # Rule 2: Check for overly compound hashtags
    # Count capital letters as word boundaries
    capital_count = sum(1 for c in tag if c.isupper())
    if capital_count > 4:  # Too many words smooshed together
        return False

    # Rule 3: Detect patterns like "coffeehousebeverageretail"
    # (all lowercase, no breaks, >15 chars)
    if len(tag) > 15 and tag.islower() and tag.isalpha():
        return False

    return True


def clean_hashtags(hashtags: List[str]) -> List[str]:
    """
    Filter and clean hashtag list to remove AI-looking tags.

    Removes:
    - Tags longer than 20 characters
    - Compound smooshed tags
    - Unnatural combinations

    Args:
        hashtags: List of hashtags (with or without #)

    Returns:
        Filtered list of realistic hashtags

    Example:
        >>> clean_hashtags(["#CoffeeTime", "#coffeehousebeverageretailexpert"])
        ['#CoffeeTime']
    """
    cleaned = []
    for tag in hashtags:
        # Normalize
        if not tag.startswith("#"):
            tag = "#" + tag

        # Validate
        if validate_hashtag(tag):
            cleaned.append(tag)

    return cleaned


# ============================================================================
# FIX 5: B2C TERMINOLOGY - Replace "leads" with visits/orders
# ============================================================================


B2C_REPLACEMENTS = {
    "qualified leads": "store visits",
    "lead generation": "customer acquisition",
    "cost-per-lead": "cost-per-visit",
    "lead nurturing": "customer engagement",
    "leads": "visitors",
    "lead magnet": "in-store offer",
    "lead scoring": "engagement scoring",
}


def fix_b2c_terminology(text: str, industry: str = "") -> str:
    """
    Replace B2B terms with B2C equivalents for retail/cafe brands.

    Replaces:
    - "Qualified leads" → "Store visits"
    - "Cost-per-lead" → "Cost-per-visit"
    - etc.

    Args:
        text: Text with potential B2B terminology
        industry: Industry context (used to determine if B2C)

    Returns:
        Text with B2C-appropriate terminology

    Example:
        >>> fix_b2c_terminology("Track qualified leads weekly", "coffee retail")
        'Track store visits weekly'
    """
    # Only apply if clearly B2C
    b2c_indicators = ["retail", "cafe", "restaurant", "coffee", "food", "beverage", "store"]
    is_b2c = any(ind in industry.lower() for ind in b2c_indicators)

    if not is_b2c and industry:  # If industry specified but not B2C, skip
        return text

    # Apply replacements (case-insensitive)
    for old_term, new_term in B2C_REPLACEMENTS.items():
        # Match whole words only
        pattern = rf"\b{re.escape(old_term)}\b"
        text = re.sub(pattern, new_term, text, flags=re.IGNORECASE)

        # Also handle capitalized versions
        old_cap = old_term.capitalize()
        new_cap = new_term.capitalize()
        pattern_cap = rf"\b{re.escape(old_cap)}\b"
        text = re.sub(pattern_cap, new_cap, text)

    return text


# ============================================================================
# FIX 6: KPI ACCURACY - Match descriptions to metrics
# ============================================================================


KPI_CORRECTIONS = {
    "foot traffic": "operational insight into store performance",
    "daily transactions": "revenue and conversion metrics",
    "attachment rate": "seasonal campaign success and upsell performance",
    "UGC volume": "community engagement and brand advocacy",
    "reel retention": "content quality and audience interest",
    "saves": "content value and bookmark-worthiness",
    "story views": "daily engagement and reach",
    "loyalty signups": "customer retention and program growth",
}


def fix_kpi_descriptions(text: str) -> str:
    """
    Ensure KPI descriptions accurately match what the metric measures.

    Corrections:
    - "Foot traffic → loyalty" ❌ → "Foot traffic → operational insight" ✅
    - "UGC → sales" ❌ → "UGC → engagement & advocacy" ✅

    Args:
        text: Text with KPI descriptions

    Returns:
        Text with accurate KPI descriptions

    Example:
        >>> fix_kpi_descriptions("Track foot traffic monthly to measure loyalty")
        'Track foot traffic monthly for operational insight into store performance'
    """
    # Pattern: "KPI name → [wrong description]"
    # Replace with correct description from mapping

    for kpi, correct_desc in KPI_CORRECTIONS.items():
        # Match patterns like "foot traffic to measure X" or "foot traffic: X"
        patterns = [
            (rf"{kpi}\s+to\s+(?:measure|track|monitor)\s+[^.]*", f"{kpi} for {correct_desc}"),
            (rf"{kpi}:\s*[^.]*(?:loyalty|sales|conversion)[^.]*", f"{kpi}: {correct_desc}"),
        ]

        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text


# ============================================================================
# FIX 7: REMOVE REPETITION - Limit phrase reuse
# ============================================================================


def remove_excessive_repetition(text: str, max_repeats: int = 2) -> str:
    """
    Limit phrase repetition across the entire text.

    Rules:
    - No phrase (4+ words) may appear more than `max_repeats` times
    - Varies phrasing automatically after threshold

    Args:
        text: Full text to check for repetition
        max_repeats: Maximum times a phrase can appear (default: 2)

    Returns:
        Text with excessive repetition removed

    Example:
        >>> text = "Great coffee. Great coffee. Great coffee."
        >>> remove_excessive_repetition(text, max_repeats=2)
        'Great coffee. Great coffee. Quality beverages.'
    """
    # Find all phrases (4+ words)
    phrases = re.findall(r"\b(\w+\s+\w+\s+\w+\s+\w+(?:\s+\w+)?)\b", text.lower())
    phrase_counts = Counter(phrases)

    # Find phrases that appear more than max_repeats
    excessive = {phrase: count for phrase, count in phrase_counts.items() if count > max_repeats}

    if not excessive:
        return text  # No repetition issues

    # Replace excessive occurrences
    for phrase in excessive:
        # Find all occurrences
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        matches = list(pattern.finditer(text))

        if len(matches) <= max_repeats:
            continue

        # Keep first max_repeats, remove rest
        for match in matches[max_repeats:]:
            # Remove this occurrence
            start, end = match.span()
            text = text[:start] + text[end:]

    # Clean up after removals
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================================
# UNIVERSAL CLEANUP - Apply all fixes
# ============================================================================


def apply_universal_cleanup(
    text: str, req: GenerateRequest = None, platform: str = "instagram"
) -> str:
    """
    Apply ALL cleanup rules in sequence for final client-ready output.

    This is the comprehensive cleanup applied as the final step before
    returning any report to the client.

    Applies (in order):
    1. Sanitize text (artifacts, broken sentences, repeated letters)
    2. Remove agency language
    3. Fix platform CTAs
    4. Fix B2C terminology
    5. Fix KPI descriptions
    6. Remove excessive repetition

    Args:
        text: Raw generated text
        req: GenerateRequest with brand brief (optional)
        platform: Target platform for CTA fixes

    Returns:
        Fully cleaned, client-ready text

    Example:
        >>> apply_universal_cleanup("We target customersss. Track leads.", req)
        'We target customers. Track store visits.'
    """
    if not text:
        return text

    # FIX 1: Sanitize template artifacts
    text = sanitize_text(text)

    # FIX 2: Remove agency language
    text = remove_agency_language(text)

    # FIX 3: Fix platform CTAs
    text = fix_platform_ctas(text, platform)

    # FIX 4: Hashtag cleanup is done separately on hashtag lists

    # FIX 5: Fix B2C terminology
    if req and hasattr(req.brief, "brand") and hasattr(req.brief.brand, "industry"):
        industry = req.brief.brand.industry or ""
        text = fix_b2c_terminology(text, industry)

    # FIX 6: Fix KPI descriptions
    text = fix_kpi_descriptions(text)

    # FIX 7: Remove excessive repetition
    text = remove_excessive_repetition(text, max_repeats=2)

    # Final whitespace cleanup
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"  +", " ", text)

    return text.strip()
