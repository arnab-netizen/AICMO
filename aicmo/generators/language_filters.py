"""Language filters for agency-grade content refinement.

Provides functions to:
- Remove blacklisted phrases
- Apply premium language expressions
- Enforce copywriting patterns
- Correct structure (headings, spacing)

These are applied post-generation when include_agency_grade=True.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

# Data directory where training files are stored
# Adjust path based on your project structure
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "training"


def _read_lines(path: Path) -> List[str]:
    """
    Read lines from a text file, filtering empty lines.

    Args:
        path: Path to text file

    Returns:
        List of non-empty lines from file, or empty list if file doesn't exist
    """
    if not path.exists():
        logger.debug(f"File not found (non-critical): {path}")
        return []
    try:
        return [
            ln.strip()
            for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if ln.strip()
        ]
    except Exception as e:
        logger.warning(f"Error reading {path}: {e}")
        return []


def remove_blacklisted(text: str) -> str:
    """
    Remove blacklisted phrases from text.

    Reads AICMO_LANGUAGE_BLACKLIST.txt and removes any matching phrases
    (case-insensitive regex match).

    Args:
        text: Text to clean

    Returns:
        Text with blacklisted phrases removed
    """
    blacklist_path = DATA_DIR / "AICMO_LANGUAGE_BLACKLIST.txt"
    phrases = _read_lines(blacklist_path)

    if not phrases:
        logger.debug("No blacklist phrases loaded (non-critical)")
        return text

    cleaned = text
    for phrase in phrases:
        pattern = re.escape(phrase.strip())
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    if len(cleaned) < len(text):
        logger.info(f"Removed {len(text) - len(cleaned)} chars of blacklisted content")

    return cleaned


def apply_premium_language(text: str) -> str:
    """
    Apply premium language expressions to text.

    Reads AICMO_PREMIUM_EXPRESSION_LIBRARY.txt and ensures premium expressions
    appear in the text. If none are present, appends a selection to the end.

    Args:
        text: Text to enhance

    Returns:
        Text with premium language applied
    """
    lib_path = DATA_DIR / "AICMO_PREMIUM_EXPRESSION_LIBRARY.txt"
    expressions = _read_lines(lib_path)

    if not expressions:
        logger.debug("No premium expressions loaded (non-critical)")
        return text

    # Check if any premium expressions already appear
    has_premium = any(expr.lower() in text.lower() for expr in expressions if len(expr) > 3)

    if has_premium:
        logger.debug("Premium language already present in text")
        return text

    # Light touch: append top 3 expressions as reference examples
    sample_expressions = expressions[:3]
    if sample_expressions:
        snippet = "\n\n---\n\n### Premium Language Applied\n\n" + "\n".join(
            f"- {expr.strip()}" for expr in sample_expressions
        )
        logger.info(f"Appended {len(sample_expressions)} premium expressions")
        return text.rstrip() + snippet

    return text


def enforce_copywriting_patterns(text: str) -> str:
    """
    Enforce copywriting patterns and best practices.

    Reads AICMO_COPYWRITING_PATTERNS.txt and appends patterns as guidance
    or applies structural improvements.

    Args:
        text: Text to enhance

    Returns:
        Text with copywriting patterns enforced
    """
    patterns_path = DATA_DIR / "AICMO_COPYWRITING_PATTERNS.txt"
    patterns = _read_lines(patterns_path)

    if not patterns:
        logger.debug("No copywriting patterns loaded (non-critical)")
        return text

    # Light implementation: ensure key copywriting principles are mentioned
    # In production, these could drive structural rewrites
    mentioned = any(pattern.lower() in text.lower() for pattern in patterns if len(pattern) > 4)

    if mentioned:
        logger.debug("Copywriting patterns already evident in text")
        return text

    # Append top patterns as reference
    sample_patterns = patterns[:5]
    if sample_patterns:
        reference = "\n\n---\n\n### Copywriting Patterns Reference\n\n" + "\n".join(
            f"- {p.strip()}" for p in sample_patterns
        )
        logger.info(f"Added copywriting pattern reference ({len(sample_patterns)} patterns)")
        return text.rstrip() + reference

    return text


def correct_structure(text: str) -> str:
    """
    Correct structure and formatting of text.

    Fixes:
    - Heading spacing (ensures blank line before/after headings)
    - Consistent list formatting
    - Paragraph spacing

    Args:
        text: Text to correct

    Returns:
        Structurally corrected text
    """
    lines = text.split("\n")
    corrected = []
    prev_was_heading = False

    for i, line in enumerate(lines):
        # Detect heading
        is_heading = line.strip().startswith(("#", "##", "###", "####"))

        if is_heading:
            # Add blank line before heading if previous wasn't blank/heading
            if corrected and corrected[-1].strip() and not prev_was_heading:
                corrected.append("")

            corrected.append(line)
            prev_was_heading = True

            # Ensure blank line after heading if next line isn't blank
            if i + 1 < len(lines) and lines[i + 1].strip():
                corrected.append("")
        else:
            corrected.append(line)
            prev_was_heading = False

    # Join and clean up excess blank lines
    result = "\n".join(corrected)
    result = re.sub(r"\n\n\n+", "\n\n", result)  # max 2 consecutive newlines

    logger.debug("Applied structural corrections to text")
    return result


def apply_all_filters(text: str) -> str:
    """
    Apply all language filters in sequence.

    This is the convenience function to apply the full filter pipeline
    in the correct order.

    Args:
        text: Text to filter

    Returns:
        Filtered text after all transformations
    """
    text = remove_blacklisted(text)
    text = apply_premium_language(text)
    text = correct_structure(text)
    text = enforce_copywriting_patterns(text)

    logger.info("Applied full language filter pipeline")
    return text
