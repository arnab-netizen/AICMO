"""Review responder generator for reputation management."""

from typing import Dict, Any, List


def parse_raw_reviews(negative_reviews_raw: str) -> List[str]:
    """
    Split raw pasted reviews into a list.

    Handles various paste formats (multiline, bullet points, etc.)
    with basic cleanup and deduplication.

    Args:
        negative_reviews_raw: Raw text pasted by operator

    Returns:
        List of individual review strings
    """
    if not negative_reviews_raw:
        return []

    # Split on blank lines or multiple line breaks
    parts = [p.strip() for p in negative_reviews_raw.split("\n") if p.strip()]

    # Remove duplicates while preserving order
    seen = set()
    unique_parts = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            unique_parts.append(p)

    return unique_parts


def generate_review_responses(
    brand: str,
    negative_reviews_raw: str,
) -> Dict[str, Any]:
    """
    Create a structure for review responses.

    Parses raw reviews and creates response placeholders.
    Actual LLM prompts for responses are wired in the main generation pipeline.

    Args:
        brand: Brand name (used in response context)
        negative_reviews_raw: Raw pasted reviews from operator

    Returns:
        Dict with 'review_responses' -> list of {review, response} dicts
    """
    reviews = parse_raw_reviews(negative_reviews_raw)
    if not reviews:
        return {"review_responses": []}

    responses = []
    for r in reviews:
        # Create schema - LLM content generated in main pipeline
        responses.append(
            {
                "review": r,
                "response": "",  # To be filled by LLM
            }
        )

    return {"review_responses": responses}
