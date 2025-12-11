"""
Quality Checkers

Validates content quality, genericity, and placeholders.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class ContentQualityCheckResult:
    """Result of content quality validation."""

    is_valid: bool
    genericity_score: float = 0.0
    """Score from 0 (generic) to 1.0 (original)"""

    repeated_phrases: List[str] = field(default_factory=list)
    """Phrases that appear multiple times"""

    placeholders_found: List[str] = field(default_factory=list)
    """Placeholder markers found"""
    
    generic_phrases_found: List[str] = field(default_factory=list)
    """Generic phrases detected"""

    warnings: List[str] = field(default_factory=list)
    """Quality warnings"""
    
    overall_quality_assessment: str = "unknown"
    """Quality assessment: excellent, good, fair, poor"""

    details: Dict[str, Any] = field(default_factory=dict)
    """Additional metrics"""


# Generic phrases that indicate low-quality content
GENERIC_PHRASES = {
    "leverage cutting-edge solutions",
    "drive engagement and growth",
    "in today's digital landscape",
    "maximize roi",
    "best-in-class",
    "synergy",
    "paradigm shift",
    "go-to-market",
    "stakeholder alignment",
    "circle back",
    "deep dive",
    "move the needle",
    "game changer",
    "innovation",
    "transformation",
    "next-level",
    "unique value proposition",
}

# Placeholder patterns
PLACEHOLDER_PATTERNS = [
    r"\[INSERT[^\]]*\]",
    r"\[TBD[^\]]*\]",
    r"\[TBA\]",
    r"\[FILL[^\]]*\]",
    r"\{[A-Z_]+\}",  # {YOUR_NAME}, {BRAND}, etc.
    r"<<[^>]+>>",  # <<SOMETHING>>
]

# Case-insensitive placeholder keywords
PLACEHOLDER_KEYWORDS = {
    "lorem ipsum",
    "placeholder",
    "tbd",
    "to be determined",
    "todo",
    "fixme",
    "tk",
    "wip",
    "[example]",
    "generic persona",
    "example objective",
    "will be populated",
    "not yet specified",
    "coming soon",
}


def check_content_quality(text: str | list) -> ContentQualityCheckResult:
    """
    Check content quality and detect generic/placeholder content.

    Args:
        text: Text to analyze (string or list of strings)

    Returns:
        ContentQualityCheckResult with quality metrics
    """
    # Convert list of texts to single string
    if isinstance(text, list):
        text = " ".join(str(t) for t in text if t)
    
    result = ContentQualityCheckResult(is_valid=True)

    if not text or not text.strip():
        result.is_valid = False
        result.warnings.append("Content is empty")
        result.genericity_score = 0.0
        return result

    text_lower = text.lower()

    # Check for placeholders
    result.placeholders_found = _find_placeholders(text)
    if result.placeholders_found:
        result.is_valid = False
        result.warnings.append(f"Found {len(result.placeholders_found)} placeholder(s)")

    # Check for generic phrases
    generic_count = 0
    for phrase in GENERIC_PHRASES:
        count = text_lower.count(phrase)
        if count > 0:
            generic_count += count
            result.generic_phrases_found.append(phrase)
            if count >= 2:
                result.repeated_phrases.append(phrase)

    # Calculate genericity score (0 = very generic, 1.0 = original)
    words_total = len(text.split())
    if words_total > 0:
        generic_ratio = generic_count / words_total
        result.genericity_score = max(0.0, 1.0 - generic_ratio)
    else:
        result.genericity_score = 0.5

    # Warnings for low originality
    if result.genericity_score < 0.5:
        result.warnings.append("Content appears very generic (low originality score)")
        result.is_valid = False
    elif result.genericity_score < 0.7:
        result.warnings.append("Content has moderate generic phrases")

    # Check for repeated sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) > 0:
        sentence_counts = {}
        for sent in sentences:
            key = sent.lower()[:50]  # First 50 chars for comparison
            sentence_counts[key] = sentence_counts.get(key, 0) + 1

        repeats = [sent for sent, count in sentence_counts.items() if count > 1]
        if repeats:
            result.warnings.append(f"Found {len(repeats)} repeated sentence(s)")

    result.details["word_count"] = words_total
    result.details["sentence_count"] = len(sentences)
    result.details["generic_phrase_count"] = generic_count
    result.details["unique_sentences"] = len(sentence_counts)

    # Set overall quality assessment
    if result.placeholders_found:
        result.overall_quality_assessment = "poor"
    elif result.genericity_score < 0.5:
        result.overall_quality_assessment = "poor"
    elif result.genericity_score < 0.7:
        result.overall_quality_assessment = "fair"
    elif result.genericity_score < 0.85:
        result.overall_quality_assessment = "good"
    else:
        result.overall_quality_assessment = "excellent"

    return result


def check_placeholder_markers(text: str) -> Dict[str, Any]:
    """
    Detect and categorize placeholder markers.

    Args:
        text: Text to scan

    Returns:
        Dictionary with placeholder detection results
    """
    result = {
        "has_placeholders": False,
        "placeholder_count": 0,
        "placeholders": [],
        "placeholder_types": {},
    }

    text_lower = text.lower()

    # Check bracket patterns
    for pattern in PLACEHOLDER_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            result["has_placeholders"] = True
            result["placeholder_count"] += len(matches)
            result["placeholders"].extend(matches)
            pattern_name = pattern[:20]  # Shortened pattern name
            result["placeholder_types"][pattern_name] = len(matches)

    # Check keyword patterns (case-insensitive)
    for keyword in PLACEHOLDER_KEYWORDS:
        if keyword in text_lower:
            result["has_placeholders"] = True
            result["placeholder_count"] += 1
            result["placeholders"].append(keyword)

    return result


def check_lexical_diversity(text: str) -> Dict[str, Any]:
    """
    Calculate lexical diversity metrics.

    Args:
        text: Text to analyze

    Returns:
        Dictionary with diversity metrics
    """
    result = {
        "unique_words": 0,
        "total_words": 0,
        "diversity_ratio": 0.0,  # unique/total
        "lexical_richness": 0.0,  # Yule's K measure (higher = more diverse)
        "is_repetitive": False,
    }

    if not text:
        return result

    words = text.lower().split()
    result["total_words"] = len(words)

    if result["total_words"] == 0:
        return result

    unique_words = len(set(words))
    result["unique_words"] = unique_words
    result["diversity_ratio"] = unique_words / result["total_words"]

    # Calculate Yule's K (measure of lexical diversity)
    # K = 10,000 * (M - N) / N^2, where M = unique words, N = total words
    if result["total_words"] > 1:
        m = unique_words
        n = result["total_words"]
        result["lexical_richness"] = (10000 * (m - n)) / (n * n) if m != n else 0

    # Flag if repetitive (diversity ratio < 0.3 means lots of repeated words)
    result["is_repetitive"] = result["diversity_ratio"] < 0.3

    return result


def _find_placeholders(text: str) -> List[str]:
    """Find all placeholder markers in text."""
    placeholders = []

    for pattern in PLACEHOLDER_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        placeholders.extend(matches)

    text_lower = text.lower()
    for keyword in PLACEHOLDER_KEYWORDS:
        if keyword in text_lower:
            # Find the actual occurrence in original text
            idx = text_lower.find(keyword)
            if idx != -1:
                placeholders.append(text[idx : idx + len(keyword)])

    return list(set(placeholders))  # Remove duplicates


def analyze_content_completeness(
    sections: Dict[str, Optional[str]],
    required_sections: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Analyze content completeness across sections.

    Args:
        sections: Dictionary of section_name -> content (or None if missing)
        required_sections: List of required section names (optional)

    Returns:
        Dictionary with completeness metrics
    """
    result = {
        "total_sections": len(sections),
        "populated_sections": 0,
        "empty_sections": [],
        "completion_percent": 0.0,
        "issues": [],
    }

    if not sections:
        return result

    for section_name, content in sections.items():
        if content and content.strip():
            result["populated_sections"] += 1
        else:
            result["empty_sections"].append(section_name)

    result["completion_percent"] = (
        (result["populated_sections"] / result["total_sections"] * 100)
        if result["total_sections"] > 0
        else 0
    )

    # Check required sections
    if required_sections:
        missing = [s for s in required_sections if sections.get(s) is None or not sections.get(s)]
        if missing:
            result["issues"].append(f"Missing required sections: {missing}")

    return result


def summarize_quality_metrics(
    quality_result: ContentQualityCheckResult,
    diversity_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Summarize quality metrics into a single score.

    Args:
        quality_result: Result from check_content_quality()
        diversity_result: Result from check_lexical_diversity()

    Returns:
        Summary dictionary with overall quality assessment
    """
    summary = {
        "overall_quality_score": 0.0,  # 0-1.0
        "quality_assessment": "unknown",  # excellent, good, fair, poor
        "components": {},
    }

    # Component scores (0-1.0)
    originality = quality_result.genericity_score
    diversity = min(1.0, diversity_result.get("diversity_ratio", 0) * 2)  # Scale to 0-1
    completeness = 1.0 if not quality_result.warnings else 0.7
    no_placeholders = 0.0 if quality_result.placeholders_found else 1.0

    summary["components"] = {
        "originality": round(originality, 2),
        "diversity": round(diversity, 2),
        "completeness": round(completeness, 2),
        "no_placeholders": round(no_placeholders, 2),
    }

    # Weighted overall score
    weights = {
        "originality": 0.3,
        "diversity": 0.2,
        "completeness": 0.3,
        "no_placeholders": 0.2,
    }

    overall = sum(
        summary["components"][key] * weights[key]
        for key in weights.keys()
    )

    summary["overall_quality_score"] = round(overall, 2)

    # Assessment label
    if summary["overall_quality_score"] >= 0.8:
        summary["quality_assessment"] = "excellent"
    elif summary["overall_quality_score"] >= 0.6:
        summary["quality_assessment"] = "good"
    elif summary["overall_quality_score"] >= 0.4:
        summary["quality_assessment"] = "fair"
    else:
        summary["quality_assessment"] = "poor"

    return summary
