"""
Genericity Penalty Scorer (v1)

This module provides lightweight, deterministic scoring to detect generic
marketing language. It doesn't rewrite anything; it just tells you when to
ask the LLM for a less-generic rewrite.
"""

from __future__ import annotations

import re
from collections import Counter
from functools import lru_cache
from typing import Iterable, Pattern


# Very small, curated list of phrases that often indicate generic / templated copy.
GENERIC_PHRASES: tuple[str, ...] = (
    "don't miss",
    "limited time",
    "flash offer",
    "quick tip",
    "in the next 30 days",
    "random acts of marketing",
    "proven methodologies",
    "tangible results",
    "measurable impact",
    "drive results",
)


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


@lru_cache(maxsize=128)
def _compile_phrase_patterns() -> list[Pattern]:
    """
    Pre-compile regex patterns for generic phrases with word boundaries.
    Handles punctuation and hyphenation variations.
    Also matches individual words to catch partial phrases.
    """
    patterns = []
    for phrase in GENERIC_PHRASES:
        words = phrase.split()
        if len(words) == 1:
            # Single word: strict word boundaries
            pattern = r"\b" + re.escape(words[0]) + r"\b"
        else:
            # Multi-word: match with flexible spacing between words
            # This catches "limited-time", "flash: offer", etc.
            pattern = r"\b" + r"[\s\W]{0,10}".join(re.escape(w) for w in words) + r"\b"
        patterns.append(re.compile(pattern, re.IGNORECASE))
    return patterns


def count_generic_phrases(text: str) -> int:
    """
    Count how many times obviously generic phrases appear in the text.
    Uses regex word boundaries to handle punctuation and hyphenation.
    """
    normalised = _normalise(text)
    patterns = _compile_phrase_patterns()
    return sum(len(pattern.findall(normalised)) for pattern in patterns)


def repetition_score(text: str, min_token_length: int = 3) -> float:
    """
    Basic repetition heuristic: measures how often non-trivial tokens repeat.

    Returns a score between 0 and 1 where higher means 'more repetitive'.
    """
    normalised = _normalise(text)
    tokens = [t for t in re.split(r"[^a-z0-9]+", normalised) if len(t) >= min_token_length]
    if not tokens:
        return 0.0
    counts = Counter(tokens)
    total = sum(counts.values())
    # Proportion of tokens that belong to words used more than twice
    repeated = sum(c for c in counts.values() if c > 2)
    return repeated / total


def genericity_score(text: str) -> float:
    """
    Compute a simple genericity score between 0 and 1.

    This is intentionally lightweight and deterministic. It can be used as a
    signal to decide whether to trigger a second, 'make this less generic'
    LLM pass.

    Heuristics used:
    - presence of hard-coded generic phrases
    - token repetition ratio
    """
    if not text or not text.strip():
        return 0.0

    gp = count_generic_phrases(text)
    rep = repetition_score(text)

    # More sensitive scoring: each phrase contributes more
    # 1 phrase = 0.23, 2 phrases = 0.47, 3+ phrases = 0.7
    phrase_component = min(gp / 3.0, 1.0)
    repetition_component = min(rep, 1.0)

    # Weighted average; tweakable later without breaking callers.
    score = phrase_component * 0.7 + repetition_component * 0.3
    return max(0.0, min(score, 1.0))


def is_too_generic(text: str, threshold: float = 0.35) -> bool:
    """
    Return True if the text is likely too generic and should be rewritten.

    The default threshold is conservative: we only flag content that clearly
    over-uses generic phrasing or repetition, to avoid unnecessary rewrites.
    """
    return genericity_score(text) >= threshold


def build_anti_generic_instruction(extra_requirements: Iterable[str] | None = None) -> str:
    """
    Helper to embed into LLM prompts when a second pass is needed.

    Example usage in a generator:

        if is_too_generic(draft):
            system_instructions.append(build_anti_generic_instruction([
                "Keep the same structure and KPIs.",
                "Use sensory, scene-based language.",
            ]))

    This keeps the integration code very small and predictable.
    """
    base = [
        "Rewrite the draft to remove generic marketing phrases and clichés.",
        "Keep the same structure, facts, and constraints, but change the wording.",
        "Avoid phrases like 'drive results', 'tangible impact', 'proven methodologies', "
        "and similar consultant-style language.",
        "Use more concrete, sensory, and brand-specific language while staying concise.",
    ]
    if extra_requirements:
        base.extend(extra_requirements)
    # Use bullet-style sentences so it's easy to drop into prompts.
    return " ".join(base)
