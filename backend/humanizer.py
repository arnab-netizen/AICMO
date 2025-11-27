# backend/humanizer.py
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, Literal, Optional

HumanizeLevel = Literal["off", "light", "medium"]


@dataclass
class HumanizerConfig:
    level: HumanizeLevel = "medium"
    max_change_ratio: float = 0.35  # <= 35% of tokens changed vs original
    preserve_headings: bool = True
    preserve_numbers: bool = True
    enable_industry_flavor: bool = True
    enable_llm: bool = False  # KEEP FALSE BY DEFAULT (no remote calls)
    min_section_length_to_edit: int = 40  # chars


# Phrases that strongly signal generic AI text; we replace them with more grounded phrasing.
GENERIC_PHRASES: Dict[str, str] = {
    r"\bin today'?s digital age\b": "right now in your market",
    r"\bholistic\b": "joined-up",
    r"\brobust\b": "reliable",
    r"\bcut through the clutter\b": "stand out from nearby competitors",
    r"\bby leveraging\b": "by using",
}

# Over-formal connectors; we vary them to sound more natural.
GENERIC_CONNECTORS: Dict[str, str] = {
    r"\bFurthermore\b": "On top of that",
    r"\bMoreover\b": "Plus",
    r"\bAdditionally\b": "You can also",
}


def apply_phrase_replacements(text: str) -> str:
    """Apply deterministic, case-insensitive replacements for generic AI-ish phrases."""
    for pattern, repl in GENERIC_PHRASES.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    for pattern, repl in GENERIC_CONNECTORS.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text


def inject_industry_flavor(text: str, industry_profile: Optional[Dict[str, object]]) -> str:
    """
    Swap some generic nouns with industry-specific ones, if configured.

    The industry_profile may define:
        word_substitutions: Dict[str, str]
    """
    if not industry_profile:
        return text

    mapping = (
        industry_profile.get("word_substitutions") if isinstance(industry_profile, dict) else None
    )
    if not isinstance(mapping, dict):
        return text

    for generic, specific in mapping.items():
        if not generic or not specific:
            continue
        text = re.sub(
            rf"\b{re.escape(str(generic))}\b",
            str(specific),
            text,
            flags=re.IGNORECASE,
        )
    return text


def normalize_sentence_lengths(text: str) -> str:
    """
    Simple heuristic to avoid very long, robotic sentences and clusters of micro-sentences.
    We only make light adjustments: split overly long sentences at 'and' or 'which'.

    IMPORTANT: We preserve paragraph structure (newlines) and only adjust within paragraphs.
    """
    # Process line by line to preserve structure
    lines = text.split("\n")
    result_lines = []

    for line in lines:
        # Skip headings and very short lines
        if line.strip().startswith("#") or len(line) < 50:
            result_lines.append(line)
            continue

        # For normal content lines, apply gentle sentence splitting
        if len(line) > 220:
            # Make one gentle split
            modified = re.sub(r"\band\b", ". And", line, count=1)
            modified = re.sub(r"\bwhich\b", ". Which", modified, count=1)
            result_lines.append(modified)
        else:
            result_lines.append(line)

    return "\n".join(result_lines)


def extract_headings(text: str) -> Dict[str, int]:
    """
    Very simple heading detector (Markdown / numbered headings / strong labels).
    We use this just as a sanity check to ensure headings survive humanization.
    """
    headings: Dict[str, int] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if (
            stripped.startswith("#")
            or stripped.endswith(":")
            or (len(stripped) > 2 and stripped[:3].isdigit())
        ):
            headings[stripped] = headings.get(stripped, 0) + 1
    return headings


def extract_numbers(text: str) -> Dict[str, int]:
    """
    Capture numeric tokens (integers, simple floats). We shouldn't lose or radically
    change these when humanizing.
    """
    numbers: Dict[str, int] = {}
    for match in re.finditer(r"\b\d+(?:\.\d+)?\b", text):
        token = match.group(0)
        numbers[token] = numbers.get(token, 0) + 1
    return numbers


def token_change_ratio(original: str, new: str) -> float:
    """
    Crude similarity metric: how many tokens differ between original and new.
    Used as a guardrail for over-editing.
    """
    o_tokens = original.split()
    n_tokens = new.split()
    if not o_tokens:
        return 0.0
    common = sum(1 for t in o_tokens if t in n_tokens)
    return 1.0 - (common / float(len(o_tokens)))


def llm_refine_style(
    report_text: str,
    brief_summary: str,
    level: HumanizeLevel,
) -> str:
    """
    Optional LLM style refinement.

    IMPORTANT:
    - This MUST be safe to disable; if OpenAI is not configured, we simply return
      the input text unmodified.
    - This function must never change structure, headings, or numbers on purpose.
    """
    # Feature flag: do not call remote APIs unless explicitly enabled.
    if not os.getenv("AICMO_ENABLE_HUMANIZER_LLM"):
        return report_text

    try:
        from openai import OpenAI  # imported lazily to avoid hard dependency if unused
    except Exception:
        return report_text

    try:
        client = OpenAI()
    except Exception:
        return report_text

    intensity = {
        "light": "make only small edits (about 10–20% of the text).",
        "medium": "rewrite phrasing moderately (about 20–35% of the text). Do not change structure.",
        "off": "make no edits and return the text as-is.",
    }.get(level, "make only small edits (about 10–20% of the text).")

    system_msg = (
        "You are an experienced senior marketing strategist editing a draft report. "
        "Your job is to improve the style so it reads like a thoughtful human wrote it. "
        "You MUST NOT add new claims, numbers, promises, or additional sections. "
        "You MUST preserve headings, section order, metrics, timelines, and budgets. "
        "Respond with ONLY the edited report text."
    )

    user_msg = f"""
Here is the brief context (for tone only):
{brief_summary}

Here is the draft report. Your task:
- keep headings and section order exactly as-is
- keep all numbers and time frames exactly as-is
- {intensity}
- remove robotic phrasing and overused AI-sounding phrases
- vary sentence length and use more natural transitions
- keep the language clear, client-ready, and professional

DRAFT REPORT:
<<<
{report_text}
>>>
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.5,
            max_tokens=8000,
        )
        content = resp.choices[0].message.content if resp.choices else None
        return content or report_text
    except Exception:
        # If anything goes wrong, we fall back to the original text.
        return report_text


def humanize_report_text(
    text: str,
    brief: object,
    pack_key: str,
    industry_key: str,
    config: Optional[HumanizerConfig] = None,
    industry_profile: Optional[Dict[str, object]] = None,
) -> str:
    """
    Main entrypoint for humanization.

    Invariants:
    - Headings should remain present.
    - Numeric tokens should not be removed.
    - Change ratio should stay below config.max_change_ratio.
    """
    if config is None:
        config = HumanizerConfig()

    if config.level == "off":
        return text

    if not text or len(text) < config.min_section_length_to_edit:
        return text

    original = text
    original_headings = extract_headings(original) if config.preserve_headings else {}
    original_numbers = extract_numbers(original) if config.preserve_numbers else {}

    # 1) Deterministic pass
    text = apply_phrase_replacements(text)
    text = normalize_sentence_lengths(text)

    if config.enable_industry_flavor and industry_profile:
        text = inject_industry_flavor(text, industry_profile)

    # 2) Optional LLM refinement (guarded by env flag & config)
    if config.enable_llm and os.getenv("AICMO_ENABLE_HUMANIZER_LLM"):
        brief_summary = getattr(brief, "primary_goal", "") or ""
        extra_context = []
        for attr in ("industry", "location", "brand_name"):
            val = getattr(brief, attr, None)
            if val:
                extra_context.append(str(val))
        if extra_context:
            brief_summary = " • ".join(extra_context) + (
                f" • goal: {brief_summary}" if brief_summary else ""
            )

        text = llm_refine_style(text, brief_summary=brief_summary, level=config.level)

    # 3) Guardrail checks; if we broke anything, fall back to deterministic-only or original.
    new_headings = extract_headings(text) if config.preserve_headings else {}
    new_numbers = extract_numbers(text) if config.preserve_numbers else {}
    ratio = token_change_ratio(original, text)

    headings_ok = not config.preserve_headings or all(
        h in new_headings for h in original_headings.keys()
    )
    numbers_ok = not config.preserve_numbers or all(
        n in new_numbers for n in original_numbers.keys()
    )
    ratio_ok = ratio <= config.max_change_ratio

    if not (headings_ok and numbers_ok and ratio_ok):
        # If guardrails fail, prefer the deterministic-only version (without LLM).
        safe = apply_phrase_replacements(original)
        safe = normalize_sentence_lengths(safe)
        if config.enable_industry_flavor and industry_profile:
            safe = inject_industry_flavor(safe, industry_profile)
        return safe

    return text
