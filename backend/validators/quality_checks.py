"""
Enhanced quality checks for AICMO content validation.

This module adds quality checks that are missing from the benchmark validator:
1. Genericity scoring (integration of is_too_generic)
2. Blacklist phrase detection
3. Duplicate hook detection in calendar sections
4. Template placeholder detection
5. Premium language verification

These checks are integrated into the validation pipeline to prevent poor-quality
outputs from passing validation.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class QualityCheckIssue:
    """Single quality issue found during validation."""

    code: str
    message: str
    severity: str = "error"  # "error" | "warning"
    details: str | None = None


def check_genericity(text: str, threshold: float = 0.35) -> QualityCheckIssue | None:
    """
    Check if content is too generic using genericity scoring.

    Integrates the is_too_generic() function from backend/genericity_scoring.py
    into the validation pipeline.

    Args:
        text: Content to check for genericity
        threshold: Maximum acceptable genericity score (0.0-1.0)

    Returns:
        QualityCheckIssue if content is too generic, None otherwise

    Example:
        >>> generic_text = "We drive results and create tangible impact through proven methodologies."
        >>> issue = check_genericity(generic_text)
        >>> issue.code
        'TOO_GENERIC'
    """
    try:
        from backend.genericity_scoring import genericity_score

        score = genericity_score(text)

        if score >= threshold:
            return QualityCheckIssue(
                code="TOO_GENERIC",
                message=f"Content is too generic (score: {score:.2f}, threshold: {threshold})",
                severity="error",
                details=(
                    "Remove generic marketing phrases like 'drive results', 'tangible impact', "
                    "'proven methodologies'. Use specific, concrete language instead."
                ),
            )
    except ImportError:
        logger.warning("genericity_scoring module not available, skipping genericity check")
    except Exception as e:
        logger.warning(f"Error during genericity check: {e}")

    return None


def check_blacklist_phrases(
    text: str, blacklist_phrases: List[str] | None = None
) -> List[QualityCheckIssue]:
    """
    Check for blacklisted phrases in content.

    Args:
        text: Content to check
        blacklist_phrases: Optional list of phrases to check. If None, uses default blacklist.

    Returns:
        List of QualityCheckIssue for each blacklisted phrase found

    Example:
        >>> text = "In today's digital age, content is king and drives engagement."
        >>> issues = check_blacklist_phrases(text)
        >>> len(issues) > 0
        True
    """
    if blacklist_phrases is None:
        # Default blacklist (common marketing clichés that AICMO avoids)
        blacklist_phrases = [
            "in today's digital age",
            "content is king",
            "drive results",
            "tangible impact",
            "proven methodologies",
            "best practices",
            "industry-leading",
            "cutting-edge",
            "state-of-the-art",
            "leverage",
            "synergy",
            "game-changer",
            "think outside the box",
            "low-hanging fruit",
            "move the needle",
            "circle back",
            "touch base",
            "deep dive",
            "at the end of the day",
            "it is what it is",
        ]

    issues: List[QualityCheckIssue] = []
    text_lower = text.lower()

    for phrase in blacklist_phrases:
        pattern = re.escape(phrase.strip())
        matches = list(re.finditer(pattern, text_lower, flags=re.IGNORECASE))

        if matches:
            issues.append(
                QualityCheckIssue(
                    code="BLACKLISTED_PHRASE",
                    message=f"Contains blacklisted phrase: '{phrase}' ({len(matches)} occurrence(s))",
                    severity="error",
                    details=f"Remove or rephrase: '{phrase}'. Use specific, concrete language instead.",
                )
            )

    return issues


def check_duplicate_hooks(content: str, section_id: str) -> QualityCheckIssue | None:
    """
    Check for duplicate hooks in calendar sections.

    This check is specific to 30-day calendar sections and ensures that each day
    has a unique hook (not repeating the same hook across multiple days).

    Args:
        content: Section content (markdown table for calendar)
        section_id: Section identifier (only runs for calendar sections)

    Returns:
        QualityCheckIssue if duplicate hooks found, None otherwise

    Example:
        >>> calendar = '''
        ... | Day 1 | Instagram | Share customer success story |
        ... | Day 2 | Instagram | Share customer success story |
        ... '''
        >>> issue = check_duplicate_hooks(calendar, "detailed_30_day_calendar")
        >>> issue.code
        'DUPLICATE_HOOKS'
    """
    # Only check calendar sections
    if section_id not in ["detailed_30_day_calendar", "social_calendar", "30_day_calendar"]:
        return None

    # Extract hooks from markdown table
    # Expected format: | Day | Platform | Hook/Content |
    hooks: List[str] = []

    for line in content.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue

        # Skip header and separator rows
        if "Day" in line and "Platform" in line:  # Header row
            continue
        if "---" in line:  # Separator row
            continue

        # Split and extract hook (3rd column, index 3 after split)
        # Split gives: ["", "Day 1", "Instagram", "Hook text", ""]
        parts = [p.strip() for p in line.split("|")]

        # Verify we have enough columns (at least 4: empty, day, platform, hook)
        if len(parts) >= 4:
            hook = parts[3].strip()  # Hook is 4th part (index 3)
            if hook and hook != "Hook":  # Skip header if not already caught
                hooks.append(hook.lower())

    if not hooks:
        logger.debug(f"No hooks found in calendar section: {section_id}")
        return None

    # Check for duplicates
    unique_hooks = set(hooks)
    duplicate_count = len(hooks) - len(unique_hooks)

    if duplicate_count > 0:
        duplicate_ratio = duplicate_count / len(hooks)

        # Allow some repetition (e.g., weekly recurring themes) but flag excessive duplication
        # Use >= instead of > to catch exactly 30% threshold
        if duplicate_ratio >= 0.3:  # 30% or more duplicates
            return QualityCheckIssue(
                code="DUPLICATE_HOOKS",
                message=f"Calendar has {duplicate_count} duplicate hooks out of {len(hooks)} total",
                severity="error",
                details=(
                    f"Duplicate ratio: {duplicate_ratio:.1%}. Each day should have a unique hook. "
                    "Ensure content varies across the 30-day calendar."
                ),
            )

    return None


def check_template_placeholders(text: str) -> List[QualityCheckIssue]:
    """
    Check for unsubstituted template placeholders.

    Detects placeholders like {{brand_name}}, [INSERT STAT], etc. that should
    have been replaced during template application.

    Args:
        text: Content to check for placeholders

    Returns:
        List of QualityCheckIssue for each placeholder type found

    Example:
        >>> text = "{{brand_name}} offers [INSERT PRODUCT] to drive results."
        >>> issues = check_template_placeholders(text)
        >>> len(issues)
        2
    """
    issues: List[QualityCheckIssue] = []

    # Check for double-brace placeholders: {{placeholder}}
    double_brace_pattern = r"\{\{[^}]+\}\}"
    double_brace_matches = re.findall(double_brace_pattern, text)

    if double_brace_matches:
        unique_placeholders = set(double_brace_matches)
        issues.append(
            QualityCheckIssue(
                code="TEMPLATE_PLACEHOLDER",
                message=f"Contains {len(double_brace_matches)} unsubstituted template placeholder(s)",
                severity="error",
                details=f"Found placeholders: {', '.join(unique_placeholders)}. "
                "All placeholders should be replaced with actual values.",
            )
        )

    # Check for [INSERT ...] patterns
    insert_pattern = r"\[INSERT[^\]]*\]"
    insert_matches = re.findall(insert_pattern, text, flags=re.IGNORECASE)

    if insert_matches:
        unique_inserts = set(insert_matches)
        issues.append(
            QualityCheckIssue(
                code="INSERT_PLACEHOLDER",
                message=f"Contains {len(insert_matches)} [INSERT ...] placeholder(s)",
                severity="error",
                details=f"Found: {', '.join(unique_inserts)}. Replace with actual content.",
            )
        )

    # Check for [BRAND] or similar bracket patterns
    bracket_pattern = r"\[(BRAND|CLIENT|COMPANY|PRODUCT|SERVICE|STAT|DATA|METRIC)\]"
    bracket_matches = re.findall(bracket_pattern, text, flags=re.IGNORECASE)

    if bracket_matches:
        unique_brackets = set(bracket_matches)
        issues.append(
            QualityCheckIssue(
                code="BRACKET_PLACEHOLDER",
                message=f"Contains {len(bracket_matches)} bracket placeholder(s)",
                severity="error",
                details=f"Found: {', '.join(f'[{b}]' for b in unique_brackets)}. "
                "Replace with actual values.",
            )
        )

    return issues


def check_premium_language(text: str, required_count: int = 1) -> QualityCheckIssue | None:
    """
    Check for presence of premium language expressions.

    AICMO reports should use premium language that elevates the copy beyond
    generic marketing speak. This check verifies that premium expressions appear.

    Args:
        text: Content to check
        required_count: Minimum number of premium expressions required

    Returns:
        QualityCheckIssue if premium language is insufficient, None otherwise

    Example:
        >>> basic_text = "We offer social media services to help your business grow."
        >>> issue = check_premium_language(basic_text)
        >>> issue.code
        'LACKS_PREMIUM_LANGUAGE'
    """
    # Premium expressions that indicate elevated copy
    premium_indicators = [
        # Sensory/concrete language
        r"\b(vibrant|vivid|crisp|tangible|crystallize|illuminate)\b",
        # Specific numbers/metrics (including percentages)
        r"\b\d+%",
        r"\b\d+x\b",
        r"\b(increased|decreased|doubled|tripled)\b.*\b\d+%",
        # Scene-based language
        r"\b(imagine|picture|envision|scene|moment)\b",
        # Metaphorical language
        r"\b(foundation|framework|blueprint|architecture|ecosystem)\b",
        # Action-oriented specifics
        r"\b(launch|deploy|execute|orchestrate|curate)\b",
    ]

    matches = 0
    for pattern in premium_indicators:
        if re.search(pattern, text, flags=re.IGNORECASE):
            matches += 1

    if matches < required_count:
        return QualityCheckIssue(
            code="LACKS_PREMIUM_LANGUAGE",
            message=f"Content lacks premium language (found {matches}, need {required_count}+)",
            severity="warning",
            details=(
                "Use more sensory, concrete, and specific language. Include specific metrics, "
                "scene-based descriptions, or metaphorical frameworks to elevate the copy."
            ),
        )

    return None


def run_all_quality_checks(
    text: str,
    section_id: str,
    genericity_threshold: float = 0.35,
    blacklist_phrases: List[str] | None = None,
) -> List[QualityCheckIssue]:
    """
    Run all quality checks on a section and return all issues found.

    This is the main entry point for quality validation. It runs all checks
    and consolidates the results.

    Args:
        text: Section content to validate
        section_id: Section identifier (for context-specific checks)
        genericity_threshold: Maximum acceptable genericity score
        blacklist_phrases: Optional custom blacklist (uses default if None)

    Returns:
        List of all QualityCheckIssue found across all checks

    Example:
        >>> text = "In today's digital age, {{brand_name}} drives results."
        >>> issues = run_all_quality_checks(text, "overview")
        >>> len(issues) >= 2  # Blacklist + placeholder
        True
    """
    all_issues: List[QualityCheckIssue] = []

    # 1. Check genericity
    genericity_issue = check_genericity(text, genericity_threshold)
    if genericity_issue:
        all_issues.append(genericity_issue)

    # 2. Check blacklist phrases
    blacklist_issues = check_blacklist_phrases(text, blacklist_phrases)
    all_issues.extend(blacklist_issues)

    # 3. Check duplicate hooks (calendar sections only)
    duplicate_issue = check_duplicate_hooks(text, section_id)
    if duplicate_issue:
        all_issues.append(duplicate_issue)

    # 4. Check template placeholders
    placeholder_issues = check_template_placeholders(text)
    all_issues.extend(placeholder_issues)

    # 5. Check premium language
    premium_issue = check_premium_language(text)
    if premium_issue:
        all_issues.append(premium_issue)

    # 6. Check hashtag format (hashtag_strategy sections only)
    hashtag_format_issues = check_hashtag_format(text, section_id)
    all_issues.extend(hashtag_format_issues)

    # 7. Check hashtag category counts (hashtag_strategy sections only)
    hashtag_count_issues = check_hashtag_category_counts(text, section_id, min_per_category=3)
    all_issues.extend(hashtag_count_issues)

    logger.info(
        "QUALITY_CHECKS_COMPLETE",
        extra={
            "section_id": section_id,
            "total_issues": len(all_issues),
            "error_count": sum(1 for i in all_issues if i.severity == "error"),
            "warning_count": sum(1 for i in all_issues if i.severity == "warning"),
        },
    )

    return all_issues


def check_hashtag_format(text: str, section_id: str) -> List[QualityCheckIssue]:
    """
    Check hashtag format for hashtag_strategy sections.

    Validates:
    - All hashtags start with #
    - Hashtags are longer than 3 characters
    - No generic/banned hashtags

    Args:
        text: Section content to check
        section_id: Section identifier

    Returns:
        List of QualityCheckIssue for format violations
    """
    issues: List[QualityCheckIssue] = []

    # Only check hashtag_strategy sections
    if section_id != "hashtag_strategy":
        return issues

    # Extract all hashtag-like tokens (words starting with # or in list items)
    hashtag_pattern = re.compile(r"#\w+")
    hashtags = hashtag_pattern.findall(text)

    # Also check for list items that should be hashtags but aren't
    # Match lines like "- word" or "* word" but not "- #hashtag"
    list_item_pattern = re.compile(r"^\s*[-*]\s+([a-zA-Z]\w+)\s*$", re.MULTILINE)
    list_items = list_item_pattern.findall(text)

    # Check for list items that don't start with #
    for item in list_items:
        # item is already just the word without spaces
        issues.append(
            QualityCheckIssue(
                code="HASHTAG_MISSING_HASH",
                message=f"Hashtag candidate missing # symbol: '{item}'",
                severity="error",
                details="All hashtags must start with #",
            )
        )

    # Banned generic hashtags (too vague, low quality)
    BANNED_GENERIC_HASHTAGS = {
        "#fun",
        "#love",
        "#summer",
        "#happy",
        "#instagood",
        "#photooftheday",
        "#beautiful",
        "#picoftheday",
        "#cute",
        "#followme",
        "#like4like",
        "#instadaily",
        "#amazing",
    }

    for hashtag in hashtags:
        hashtag_lower = hashtag.lower()

        # Check minimum length (must be >= 4 chars including #, i.e., #ABC)
        if len(hashtag) < 4:
            issues.append(
                QualityCheckIssue(
                    code="HASHTAG_TOO_SHORT",
                    message=f"Hashtag too short: '{hashtag}' (must be >= 4 characters)",
                    severity="error",
                    details="Hashtags must be at least 4 characters including the # symbol",
                )
            )

        # Check for banned generic hashtags
        if hashtag_lower in BANNED_GENERIC_HASHTAGS:
            issues.append(
                QualityCheckIssue(
                    code="HASHTAG_TOO_GENERIC",
                    message=f"Banned generic hashtag detected: '{hashtag}'",
                    severity="error",
                    details=f"Avoid vague hashtags like {hashtag}. Use specific, brand/industry-relevant tags.",
                )
            )

    return issues


def check_hashtag_category_counts(
    text: str, section_id: str, min_per_category: int = 3
) -> List[QualityCheckIssue]:
    """
    Check that each hashtag category has minimum required tags.

    Args:
        text: Section content to check
        section_id: Section identifier
        min_per_category: Minimum hashtags required per category

    Returns:
        List of QualityCheckIssue for count violations
    """
    issues: List[QualityCheckIssue] = []

    # Only check hashtag_strategy sections
    if section_id != "hashtag_strategy":
        return issues

    # Find each category section and count hashtags
    categories = {
        "Brand Hashtags": 0,
        "Industry Hashtags": 0,
        "Campaign Hashtags": 0,
    }

    # Split into sections by ## or ### headers (more permissive)
    lines = text.split("\n")
    current_category = None

    for line in lines:
        # Check if this line is a category header (level-2 or level-3)
        stripped = line.strip()
        if stripped.startswith("### "):
            header = stripped[4:].strip()
            if header in categories:
                current_category = header
        elif stripped.startswith("## "):
            header = stripped[3:].strip()
            if header in categories:
                current_category = header
        # Count hashtags in current category
        elif current_category and line.strip():
            # Count lines that contain hashtags (with or without list markers)
            if "#" in line and len(line.strip()) > 1:
                # This line has a hashtag, count it
                hashtag_matches = re.findall(r"#\w+", line)
                categories[current_category] += len(hashtag_matches)

    # Check minimums
    for category, count in categories.items():
        if count < min_per_category:
            issues.append(
                QualityCheckIssue(
                    code="HASHTAG_INSUFFICIENT_COUNT",
                    message=f"{category} has {count} hashtags, minimum is {min_per_category}",
                    severity="error",
                    details=f"Each hashtag category must have at least {min_per_category} hashtags",
                )
            )

    return issues
