"""
Humanization Helpers – Phase 6

Simple, lightweight helpers to make outbound messaging feel more natural
and less obviously AI-generated.

These are intentionally simple and deterministic (no randomization needed).
"""

from typing import List, Optional


def sanitize_message_to_avoid_ai_markers(text: Optional[str]) -> str:
    """
    Sanitize text to remove obvious AI markers and disclaimers.
    
    Removes phrases like:
    - "As an AI"
    - "I am an artificial intelligence"
    - "This is an AI-generated message"
    - "I cannot"
    - "As a language model"
    
    Args:
        text: Input text (may be None or empty)
        
    Returns:
        Cleaned text with AI markers removed
        
    Example:
        >>> text = "As an AI assistant, I cannot make promises."
        >>> sanitize_message_to_avoid_ai_markers(text)
        "I cannot make promises."
    """
    
    if not text:
        return ""
    
    # Markers to remove
    ai_markers = [
        "As an AI",
        "As an artificial intelligence",
        "I am an artificial intelligence",
        "I am an AI",
        "This is an AI-generated message",
        "AI-generated",
        "As a language model",
        "I'm a language model",
        "I apologize, but as an AI",
        "I cannot provide",
        "I'm unable to",
        "I must inform you",
        "Please note that I am an AI",
    ]
    
    result = text
    
    for marker in ai_markers:
        # Case-insensitive replacement
        result = result.replace(marker, "")
        result = result.replace(marker.lower(), "")
        result = result.replace(marker.upper(), "")
    
    # Clean up extra whitespace
    result = " ".join(result.split())
    
    return result.strip()


def pick_variant(options: List[str]) -> str:
    """
    Pick a variant from a list of options.
    
    For now, this is deterministic (picks first non-empty option).
    Future: Can add light variation without randomization (e.g., swap word order).
    
    Args:
        options: List of text options
        
    Returns:
        First non-empty option, or empty string if all are empty
        
    Example:
        >>> options = ["", "Hello", "Hi"]
        >>> pick_variant(options)
        "Hello"
    """
    
    if not options:
        return ""
    
    # Return first non-empty option
    for option in options:
        if option and option.strip():
            return option.strip()
    
    return ""


def lighten_tone(text: str, remove_urgency: bool = True) -> str:
    """
    Lighten the tone of marketing text.
    
    Optionally removes urgent/pushy language like:
    - "URGENT"
    - "LIMITED TIME"
    - "ACT NOW"
    - "Don't miss out"
    
    Args:
        text: Input text
        remove_urgency: If True, remove urgent language
        
    Returns:
        Text with lighter tone
    """
    
    if not text:
        return ""
    
    result = text
    
    if remove_urgency:
        urgent_phrases = [
            "URGENT:",
            "LIMITED TIME:",
            "ACT NOW",
            "DON'T MISS OUT",
            "LAST CHANCE",
            "HURRY",
            "ONLY TODAY",
        ]
        
        for phrase in urgent_phrases:
            result = result.replace(phrase, "")
            result = result.replace(phrase.lower(), "")
            result = result.replace(phrase.title(), "")
    
    # Clean up
    result = " ".join(result.split())
    return result.strip()


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATION HELPERS
# ─────────────────────────────────────────────────────────────────────────────


def apply_humanization_to_outbound_text(text: str) -> str:
    """
    Apply all humanization helpers to outbound text.
    
    This is the main entry point for post-processing messages
    before they are sent out via any gateway.
    
    Args:
        text: Raw text to humanize
        
    Returns:
        Humanized text
        
    Example:
        >>> raw = "As an AI, here is an urgent message: ACT NOW!"
        >>> apply_humanization_to_outbound_text(raw)
        "here is an message"
    """
    
    if not text:
        return ""
    
    # Step 1: Remove AI markers
    result = sanitize_message_to_avoid_ai_markers(text)
    
    # Step 2: Lighten tone (optional)
    result = lighten_tone(result, remove_urgency=True)
    
    return result
