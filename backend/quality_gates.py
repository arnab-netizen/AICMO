"""
Quality Gates and Sanitizers for Report Output

This module provides functions to:
1. Sanitize final report text (remove debug markers, internal notes, unfilled placeholders)
2. Gate learning on report quality (reject reports with placeholders, errors, internal notes)
3. Validate reports before sending to clients

All functions are defensive and non-blocking to the main generation flow.
"""

import re
import logging
from typing import Tuple, List

logger = logging.getLogger("aicmo.quality")


def sanitize_final_report_text(text: str) -> str:
    """
    Remove internal markers, debug notes, unfilled placeholders from final client report.

    This is the last cleanup pass before returning to client or learning system.

    Removes:
    - [This section was missing. AICMO auto-generated it...]
    - [Error generating ...]
    - Diagnostic markers
    - Unfilled {{placeholder}} patterns
    - Excessive blank lines

    Args:
        text: Full report markdown text

    Returns:
        Cleaned report text safe for client viewing
    """
    if not text:
        return text

    result = text

    # 1. Remove internal auto-generation note
    result = re.sub(
        r"\[This section was missing\..*?based on training libraries\.\]",
        "",
        result,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # 2. Remove error message markers
    result = re.sub(r"\[Error generating [^\]]*\]", "", result, flags=re.IGNORECASE)

    # 3. Remove diagnostic/debug markers (lines with "===", "---" only)
    result = re.sub(r"^[-=]{10,}$", "", result, flags=re.MULTILINE)

    # 4. Remove unfilled template placeholders ({{placeholder}})
    result = re.sub(r"\{\{[a-zA-Z0-9_]+\}\}", "", result)

    # 5. Remove unfilled bracket placeholders
    result = re.sub(
        r"\[(?:Brand Name|Founder Name|insert [^\]]+)\]", "", result, flags=re.IGNORECASE
    )

    # 6. Remove "Not specified" placeholders
    result = re.sub(r"\bNot specified\b", "", result, flags=re.IGNORECASE)

    # 7. Collapse excessive blank lines (3+ becomes 2)
    result = re.sub(r"\n\n\n+", "\n\n", result)

    # 8. Remove lines that are just whitespace
    result = re.sub(r"^[ \t]+$", "", result, flags=re.MULTILINE)

    # 9. Clean up edge cases (content starting/ending with dashes)
    result = result.strip("-").strip()

    return result.strip()


def is_report_learnable(full_text: str, brief_brand_name: str = "") -> Tuple[bool, List[str]]:
    """
    Quality gate: Check if a report is safe to add to learning system.

    Rejects reports that contain:
    - Placeholder tokens: [Brand Name], {{brand_name}}, [Founder Name], etc.
    - Generic phrases: your industry, your category, your audience
    - Error markers: "Error generating", "object has no attribute", "Traceback"
    - Internal notes: "This section was missing", "not yet implemented"
    - Missing critical fields: empty brand_name

    Args:
        full_text: Complete report markdown
        brief_brand_name: The brand name from the brief (for validation)

    Returns:
        Tuple of (is_learnable: bool, rejection_reasons: List[str])
        If is_learnable=True, reasons list will be empty
        If is_learnable=False, reasons explain why report failed quality gate
    """
    reasons = []

    # Check 1: Brand name validation
    if not brief_brand_name or not brief_brand_name.strip():
        reasons.append("Missing or empty brand_name")

    # Check 2: Placeholder markers
    placeholder_patterns = [
        (r"\[Brand Name\]", "[Brand Name] placeholder"),
        (r"\[Founder Name\]", "[Founder Name] placeholder"),
        (r"\{\{[a-zA-Z0-9_]+\}\}", "{{placeholder}} unfilled"),
        (r"\[insert [^\]]+\]", "[insert ...] placeholder"),
    ]
    for pattern, desc in placeholder_patterns:
        if re.search(pattern, full_text, re.IGNORECASE):
            reasons.append(f"Contains {desc}")

    # Check 3: Generic phrases
    generic_phrases = [
        (r"\byour industry\b", "your industry"),
        (r"\byour category\b", "your category"),
        (r"\byour audience\b", "your audience"),
        (r"\byour market\b", "your market"),
        (r"\byour space\b", "your space"),
    ]
    for pattern, desc in generic_phrases:
        if re.search(pattern, full_text, re.IGNORECASE):
            reasons.append(f"Contains generic phrase: {desc}")

    # Check 4: Error markers
    error_patterns = [
        (r"Error generating", "Error message"),
        (r"object has no attribute", "Python AttributeError"),
        (r"Traceback \(most recent call last\)", "Stack trace"),
        (r"Exception:", "Exception marker"),
    ]
    for pattern, desc in error_patterns:
        if re.search(pattern, full_text):
            reasons.append(f"Contains {desc}")

    # Check 5: Internal notes
    internal_patterns = [
        (r"This section was missing", "Internal auto-generation note"),
        (r"not yet implemented", "Not implemented marker"),
        (r"TODO", "TODO marker"),
        (r"FIXME", "FIXME marker"),
    ]
    for pattern, desc in internal_patterns:
        if re.search(pattern, full_text, re.IGNORECASE):
            reasons.append(f"Contains {desc}")

    # Check 6: Minimum length (reject tiny outputs)
    if len(full_text) < 500:
        reasons.append(f"Report too short ({len(full_text)} chars, min 500)")

    # If any reasons found, report is not learnable
    is_learnable = len(reasons) == 0

    return is_learnable, reasons


def validate_report_for_client(full_text: str) -> Tuple[bool, List[str]]:
    """
    Validate report before sending to client.

    Similar to is_report_learnable but focused on client-facing issues:
    - Error messages must not appear
    - Placeholders must be filled or removed
    - No internal notes should be visible

    Does NOT check for brand_name presence (client can still fix that).

    Args:
        full_text: Complete report markdown

    Returns:
        Tuple of (is_valid: bool, issues: List[str])
    """
    issues = []

    # Critical issues that must not appear in client output
    critical_patterns = [
        (r"Error generating", "Error message exposed"),
        (r"object has no attribute", "Python error exposed"),
        (r"Traceback", "Stack trace exposed"),
        (r"\[Error", "Error marker exposed"),
    ]

    for pattern, desc in critical_patterns:
        if re.search(pattern, full_text):
            issues.append(desc)

    # Warning issues (should be cleaned but not blocking)
    warning_patterns = [
        (r"\[Brand Name\]", "[Brand Name] unfilled"),
        (r"\{\{[a-zA-Z0-9_]+\}\}", "{{placeholder}} unfilled"),
        (r"This section was missing", "Internal note visible"),
    ]

    for pattern, desc in warning_patterns:
        if re.search(pattern, full_text):
            issues.append(f"Warning: {desc}")

    # Report is valid if no critical issues
    is_valid = not any(
        "Error message" in issue or "Python error" in issue or "Stack trace" in issue
        for issue in issues
    )

    return is_valid, issues
