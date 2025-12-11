"""
Format Checkers

Validates text format, word counts, and structure of outputs.
Supports deep field extraction from nested objects and provides
comprehensive word-count validation across client-facing outputs.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TextFormatCheckResult:
    """Result of text format validation."""

    is_valid: bool
    too_short_fields: List[str] = field(default_factory=list)
    too_long_fields: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    """Detailed metrics per field: word_count, char_count, line_count, etc."""


# Enhanced thresholds for different field types - based on realistic expectations
THRESHOLDS = {
    # Executive/summary fields - need substantial content
    "executive_summary": {"min_words": 40, "max_words": 400},
    "summary": {"min_words": 30, "max_words": 300},
    "overview": {"min_words": 25, "max_words": 250},
    
    # Strategic content
    "strategy": {"min_words": 50, "max_words": 500},
    "situation_analysis": {"min_words": 40, "max_words": 400},
    "analysis": {"min_words": 30, "max_words": 350},
    "key_insights": {"min_words": 20, "max_words": 200},
    "insight": {"min_words": 15, "max_words": 150},
    
    # Messaging and positioning
    "core_message": {"min_words": 10, "max_words": 100},
    "value_proposition": {"min_words": 15, "max_words": 150},
    "promise": {"min_words": 5, "max_words": 50},
    "positioning": {"min_words": 10, "max_words": 100},
    
    # Descriptions and narratives
    "description": {"min_words": 10, "max_words": 200},
    "narrative": {"min_words": 20, "max_words": 250},
    "story": {"min_words": 20, "max_words": 250},
    "conflict": {"min_words": 5, "max_words": 75},
    "resolution": {"min_words": 5, "max_words": 75},
    
    # Social media content
    "caption": {"min_words": 5, "max_words": 100},
    "hook": {"min_words": 3, "max_words": 30},
    "cta": {"min_words": 2, "max_words": 20},
    "call_to_action": {"min_words": 2, "max_words": 20},
    
    # Persona and audience
    "persona": {"min_words": 20, "max_words": 300},
    "audience": {"min_words": 15, "max_words": 150},
    "demographics": {"min_words": 10, "max_words": 100},
    "psychographics": {"min_words": 10, "max_words": 150},
    "pain_points": {"min_words": 10, "max_words": 100},
    "motivations": {"min_words": 10, "max_words": 100},
    
    # Headlines and titles
    "headline": {"min_words": 3, "max_words": 15},
    "title": {"min_words": 3, "max_words": 15},
    "theme": {"min_words": 3, "max_words": 20},
    
    # Bullet points and short content
    "bullet": {"min_words": 3, "max_words": 30},
    "point": {"min_words": 3, "max_words": 30},
    
    # Longer form content
    "paragraph": {"min_words": 40, "max_words": 300},
    "objective": {"min_words": 10, "max_words": 100},
    
    # Default/fallback for unrecognized field types
    "generic": {"min_words": 2, "max_words": 500},
}


def count_words(text: str) -> int:
    """Count words in text (simple split on whitespace)."""
    if not text:
        return 0
    return len(text.split())


def count_sentences(text: str) -> int:
    """Count sentences (rough heuristic)."""
    if not text:
        return 0
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])


def _extract_text_fields(
    obj: Any,
    path: str = "",
    result: Optional[Dict[str, str]] = None,
    max_depth: int = 5,
    current_depth: int = 0,
    skip_paths: Optional[set] = None
) -> Dict[str, str]:
    """
    Recursively extract all string fields from nested dict/object structures.
    
    Handles Pydantic models, dicts, lists, and dataclasses. Useful for
    validating all text content in complex nested output objects.
    
    Args:
        obj: Object to extract from (dict, Pydantic model, dataclass, etc.)
        path: Current path in object tree (dot-separated, e.g., "strategy.overview")
        result: Accumulator dict for extracted fields
        max_depth: Stop recursion at this depth (prevents infinite recursion)
        current_depth: Current recursion depth
        skip_paths: Set of field names to skip (e.g., {"id", "created_at"})
    
    Returns:
        Dict mapping field paths to their string values
    """
    if result is None:
        result = {}
    if skip_paths is None:
        skip_paths = {"id", "created_at", "updated_at", "version", "status"}
    
    # Stop recursing if too deep
    if current_depth >= max_depth:
        return result
    
    # Handle Pydantic models - convert to dict
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump()
    elif hasattr(obj, "__dict__") and not isinstance(obj, (str, int, float, bool, list, dict, type)):
        obj = obj.__dict__
    
    # Process dictionaries
    if isinstance(obj, dict):
        for key, value in obj.items():
            # Skip metadata fields
            if key in skip_paths:
                continue
            
            field_path = f"{path}.{key}" if path else key
            
            if isinstance(value, str) and value.strip():
                # Store non-empty string values
                result[field_path] = value
            elif isinstance(value, (dict, list)):
                # Recurse into nested structures
                if isinstance(value, dict):
                    _extract_text_fields(value, field_path, result, max_depth, current_depth + 1, skip_paths)
                elif isinstance(value, list) and value:
                    # For lists, process each item
                    for i, item in enumerate(value[:10]):  # Limit to first 10 items
                        if isinstance(item, (dict, str)):
                            item_path = f"{field_path}[{i}]"
                            if isinstance(item, str) and item.strip():
                                result[item_path] = item
                            elif isinstance(item, dict):
                                _extract_text_fields(item, item_path, result, max_depth, current_depth + 1, skip_paths)
    
    return result


def check_text_format(
    fields: Any = None,
    field_types: Optional[Dict[str, str]] = None,
    data: Optional[Any] = None,
    custom_thresholds: Optional[Dict[str, Dict[str, int]]] = None,
) -> TextFormatCheckResult:
    """
    Check text format and word counts.

    Supports two calling conventions:
    1. Legacy: check_text_format(fields=dict_of_fields, field_types=dict_of_types)
    2. New: check_text_format(data=pydantic_model_or_dict)

    Args:
        fields: Dictionary of field_name -> text_content (legacy API)
        field_types: Optional dict of field_name -> field_type (legacy API)
        data: Object to extract and validate (Pydantic model, dict, etc.) (new API)
        custom_thresholds: Optional dict to override/extend default THRESHOLDS

    Returns:
        TextFormatCheckResult with validation details
    """
    result = TextFormatCheckResult(is_valid=True)
    thresholds = THRESHOLDS.copy()
    if custom_thresholds:
        thresholds.update(custom_thresholds)

    # Support both old and new API
    if data is not None:
        # New API: extract fields from data
        fields = _extract_text_fields(data)
        field_types = {}
    elif fields is None:
        result.warnings.append("No fields provided to validate")
        return result

    if not fields:
        result.warnings.append("No text fields to validate")
        return result

    field_types = field_types or {}

    for field_name, text_content in fields.items():
        if not text_content or not isinstance(text_content, str):
            result.warnings.append(f"Field '{field_name}' is empty or not a string")
            continue

        # Infer field type if not provided
        field_type = field_types.get(field_name, _infer_field_type(field_name))

        # Count words
        word_count = count_words(text_content)
        char_count = len(text_content)
        line_count = len(text_content.split("\n"))
        sentence_count = count_sentences(text_content)

        # Get thresholds for this field type (fall back to generic if not found)
        if field_type in thresholds:
            threshold = thresholds[field_type]
        elif field_type != "generic" and "generic" in thresholds:
            threshold = thresholds["generic"]
            field_type = "generic"  # Update field type for consistent reporting
        else:
            threshold = {"min_words": 0, "max_words": float("inf")}

        min_words = threshold.get("min_words", 0)
        max_words = threshold.get("max_words", float("inf"))

        # Store metrics with thresholds
        result.metrics[field_name] = {
            "word_count": word_count,
            "char_count": char_count,
            "line_count": line_count,
            "sentence_count": sentence_count,
            "field_type": field_type,
            "min_required": min_words,
            "max_allowed": max_words,
        }

        # Check against thresholds
        if word_count < min_words:
            result.too_short_fields.append(field_name)
            result.metrics[field_name]["issue"] = f"too_short: {word_count} < {min_words}"
            result.is_valid = False
        elif word_count > max_words:
            result.too_long_fields.append(field_name)
            result.metrics[field_name]["issue"] = f"too_long: {word_count} > {max_words}"
            result.is_valid = False  # Too long also invalidates the result

    return result


def check_structure(
    text: str,
    expected_sections: Optional[List[str]] = None,
    expected_bullets: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Check structural aspects of text.

    Args:
        text: Text to analyze
        expected_sections: List of section headers to look for (case-insensitive)
        expected_bullets: Minimum number of bullet points expected

    Returns:
        Dictionary with structure metrics
    """
    result = {
        "is_valid": True,
        "issues": [],
        "sections_found": [],
        "bullet_count": 0,
        "paragraph_count": 0,
    }

    if not text:
        result["is_valid"] = False
        result["issues"].append("Text is empty")
        return result

    # Count bullets
    import re
    bullets = re.findall(r'^[\s]*[-•*]\s', text, re.MULTILINE)
    result["bullet_count"] = len(bullets)

    # Count paragraphs (split by double newline)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    result["paragraph_count"] = len(paragraphs)

    # Look for expected sections
    if expected_sections:
        text_lower = text.lower()
        for section in expected_sections:
            if section.lower() in text_lower:
                result["sections_found"].append(section)

        missing = set(expected_sections) - set(result["sections_found"])
        if missing:
            result["is_valid"] = False
            result["issues"].append(f"Missing sections: {', '.join(missing)}")

    # Check bullet count
    if expected_bullets is not None:
        if result["bullet_count"] < expected_bullets:
            result["is_valid"] = False
            result["issues"].append(
                f"Only {result['bullet_count']} bullets (expected >= {expected_bullets})"
            )

    return result


def _infer_field_type(field_name: str) -> str:
    """
    Infer field type from field name.

    Args:
        field_name: Name of the field

    Returns:
        Field type (summary, caption, strategy, etc.)
    """
    name_lower = field_name.lower()

    if "summary" in name_lower:
        return "summary"
    elif "caption" in name_lower or "post" in name_lower:
        return "caption"
    elif "headline" in name_lower or "title" in name_lower:
        return "headline"
    elif "strategy" in name_lower:
        return "strategy"
    elif "insight" in name_lower or "analysis" in name_lower:
        return "insight"
    elif "bullet" in name_lower or "point" in name_lower:
        return "bullet"
    elif "description" in name_lower:
        return "description"
    elif "objective" in name_lower:
        return "objective"
    elif "paragraph" in name_lower:
        return "paragraph"
    else:
        return "generic"


def validate_calendar_format(
    calendar_entries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validate social calendar entries format.

    Args:
        calendar_entries: List of calendar entries

    Returns:
        Dictionary with validation results
    """
    result = {
        "is_valid": True,
        "total_entries": len(calendar_entries),
        "issues": [],
        "entry_metrics": [],
    }

    if not calendar_entries:
        result["issues"].append("Calendar is empty")
        return result

    for idx, entry in enumerate(calendar_entries):
        entry_result = {
            "index": idx,
            "platform": entry.get("platform", "unknown"),
            "has_content": False,
            "content_length": 0,
            "issues": [],
        }

        # Check for required fields
        if "date" not in entry:
            entry_result["issues"].append("Missing 'date' field")
        if "content" not in entry:
            entry_result["issues"].append("Missing 'content' field")
        else:
            content = entry.get("content", "")
            if content:
                entry_result["has_content"] = True
                entry_result["content_length"] = len(content.split())

                # Check for minimum content
                if entry_result["content_length"] < 3:
                    entry_result["issues"].append(
                        f"Content too short: {entry_result['content_length']} words"
                    )

        if entry_result["issues"]:
            result["is_valid"] = False

        result["entry_metrics"].append(entry_result)

    return result


def validate_list_completeness(
    items: List[Any],
    min_items: int = 3,
    expected_keys: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Validate list completeness.

    Args:
        items: List of items to validate
        min_items: Minimum number of items expected
        expected_keys: If items are dicts, check for these keys

    Returns:
        Dictionary with validation results
    """
    result = {
        "is_valid": True,
        "item_count": len(items),
        "issues": [],
    }

    if len(items) < min_items:
        result["is_valid"] = False
        result["issues"].append(f"Only {len(items)} items (expected >= {min_items})")

    if expected_keys and items and isinstance(items[0], dict):
        for idx, item in enumerate(items):
            missing_keys = [k for k in expected_keys if k not in item]
            if missing_keys:
                result["is_valid"] = False
                result["issues"].append(f"Item {idx} missing keys: {missing_keys}")

    return result
