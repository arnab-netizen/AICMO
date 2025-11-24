from __future__ import annotations

import os
import random
import textwrap
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

try:
    from openai import OpenAI  # type: ignore
except ImportError:  # keep backend safe if openai not installed
    OpenAI = None  # type: ignore


def _get_openai_client() -> Optional["OpenAI"]:
    """
    Safe helper: return OpenAI client or None if not available.
    Relies on OPENAI_API_KEY in env (same pattern as the rest of AICMO).
    """
    if OpenAI is None:
        return None
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def _call_llm(
    prompt: str,
    *,
    model: Optional[str] = None,
    max_output_tokens: int = 800,
) -> Optional[str]:
    """
    Thin adapter that calls OpenAI chat.completions.

    Returns None on any failure so the caller can gracefully degrade.
    """
    client = _get_openai_client()
    if client is None:
        return None

    model_name = model or os.environ.get("AICMO_HUMANIZER_MODEL") or "gpt-4o-mini"

    try:
        # Chat Completions API
        if hasattr(client, "chat"):
            chat_resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=max_output_tokens,
            )
            choice = chat_resp.choices[0]
            return choice.message.content

    except Exception:
        # Fail soft: caller will use original text
        return None

    return None


@dataclass
class PersonaConfig:
    """
    Configuration for the persona / tone used in the humanization layer.
    """

    name: str = "Senior Brand Strategist"
    description: str = (
        "You are a senior brand strategist who has led campaigns "
        "for global and high-growth brands. You are opinionated, "
        "practical, and allergic to vague marketing clichés."
    )
    style_notes: str = (
        "Write in clear, natural language. Vary sentence length. "
        "Prefer specifics over buzzwords. Do not sound like a template. "
        "Use occasional rhetorical questions or short punchy lines "
        "only where they genuinely help."
    )


class HumanizationWrapper:
    """
    Wrapper that applies three layers:

    1) Humanization (strip obvious AI patterns)
    2) Variation / imperfection injection
    3) Persona-layer rewrite

    Safe by default:
    - If OpenAI is not configured or fails, it falls back to
      a minimal heuristic cleaner and returns original text.
    """

    def __init__(
        self,
        persona: Optional[PersonaConfig] = None,
        model: Optional[str] = None,
    ) -> None:
        self.persona = persona or PersonaConfig()
        self.model = model

    # ---- Public API -------------------------------------------------

    def process_text(
        self,
        text: str,
        *,
        brand_voice: Optional[str] = None,
        extra_context: Optional[str] = None,
    ) -> str:
        """
        Main entry point: feed raw LLM output and get humanized text back.
        """
        if not text or not text.strip():
            return text

        # 1) Humanization pass via LLM (if available)
        draft = self._humanize_pass(text, brand_voice=brand_voice, extra_context=extra_context)

        # 2) Micro-variation / imperfection injection (pure Python)
        draft = self._inject_variation(draft)

        # 3) Persona-layer rewrite (LLM, best-effort)
        draft = self._persona_rewrite(draft, brand_voice=brand_voice, extra_context=extra_context)

        return draft

    def process_report(
        self,
        report: Dict[str, Any],
        *,
        fields: Optional[Sequence[str]] = None,
        brand_voice: Optional[str] = None,
        extra_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Convenience helper:
        Humanize a whole report dict in-place for selected fields.

        Example:
            report = wrapper.process_report(
                report,
                fields=["executive_summary", "strategy", "copy_variants"],
            )
        """
        if fields is None:
            # conservative default: common text-y fields
            fields = (
                "executive_summary",
                "strategy",
                "insights",
                "recommendations",
                "copy",
                "copy_variants",
                "body",
            )

        new_report = dict(report)

        for field in fields:
            if field not in new_report:
                continue

            value = new_report[field]
            if isinstance(value, str):
                new_report[field] = self.process_text(
                    value,
                    brand_voice=brand_voice,
                    extra_context=extra_context,
                )
            elif isinstance(value, list) and all(isinstance(x, str) for x in value):
                new_report[field] = [
                    self.process_text(
                        x,
                        brand_voice=brand_voice,
                        extra_context=extra_context,
                    )
                    for x in value
                ]

        return new_report

    # ---- Layer 1: Humanization pass --------------------------------

    def _humanize_pass(
        self,
        text: str,
        *,
        brand_voice: Optional[str],
        extra_context: Optional[str],
    ) -> str:
        """
        Use LLM to strip the obvious AI "template" style.
        """
        prompt_parts = [
            "Rewrite the following so it reads like a human expert wrote it.",
            "",
            "Goals:",
            "- Remove generic AI patterns such as:",
            "  * 'Here are some ways' / 'In conclusion' boilerplate",
            "  * Overly formal or symmetric sentence structures",
            "  * Over-explaining obvious points",
            "- Make it sound natural, confident, and grounded.",
            "",
            "Constraints:",
            "- Do NOT change the underlying meaning or claims.",
            "- Keep it suitable for a professional brand/marketing context.",
        ]

        if brand_voice:
            prompt_parts.append("")
            prompt_parts.append(f"Brand voice to respect: {brand_voice}")

        if extra_context:
            prompt_parts.append("")
            prompt_parts.append(f"Context: {extra_context}")

        prompt_parts.append("")
        prompt_parts.append("Text to rewrite:")
        prompt_parts.append(text)

        prompt = "\n".join(prompt_parts)

        # ✨ FIX #4: Increased max_tokens from 800 to 4000 for full report humanization
        resp = _call_llm(prompt, model=self.model, max_output_tokens=4000)
        if resp is None:
            # Fallback: minimal cleanup
            return self._fast_cleanup(text)
        return resp.strip() or text

    # ---- Layer 2: Variation / imperfection --------------------------

    def _inject_variation(self, text: str) -> str:
        """
        Lightweight heuristics to break the "perfectly neat" AI cadence.
        Pure Python; no external calls.
        """
        if not text:
            return text

        # Rough sentence splitting (crude but good enough)
        sentences = [
            s.strip() for s in text.replace("?", "?.").replace("!", "!.").split(".") if s.strip()
        ]
        if len(sentences) <= 2:
            return text  # nothing to do

        adjusted: List[str] = []
        for idx, s in enumerate(sentences):
            # Occasionally shorten a sentence by splitting it
            if "," in s and random.random() < 0.12:
                parts = [p.strip() for p in s.split(",") if p.strip()]
                if len(parts) >= 2:
                    adjusted.append(parts[0])
                    adjusted.append(", ".join(parts[1:]))
                    continue

            # Occasionally add a rhetorical question after a key sentence
            adjusted.append(s)
            if (
                idx in (1, 2)  # early in the text
                and random.random() < 0.25
                and not s.endswith("?")
            ):
                adjusted.append("Does that really move the needle?")

        # Rejoin with some variation
        rebuilt = ". ".join(adjusted)
        if not rebuilt.endswith((".", "?", "!")):
            rebuilt += "."

        return rebuilt

    # ---- Layer 3: Persona rewrite ----------------------------------

    def _persona_rewrite(
        self,
        text: str,
        *,
        brand_voice: Optional[str],
        extra_context: Optional[str],
    ) -> str:
        """
        Final persona pass to give it a stable "human strategist" fingerprint.
        """
        prompt_parts = [
            self.persona.description,
            "",
            self.persona.style_notes,
            "",
            "Task:",
            "Take the text below and lightly rewrite it so it feels like it came from",
            f"a {self.persona.name}. Preserve structure and key points, but:",
            "- Make choices where a human would (prioritise what matters).",
            "- Remove any remaining clichés or padding.",
            "- It's okay to sound slightly opinionated.",
        ]

        if brand_voice:
            prompt_parts.append("")
            prompt_parts.append(f"Brand voice guidelines: {brand_voice}")

        if extra_context:
            prompt_parts.append("")
            prompt_parts.append(f"Additional context: {extra_context}")

        prompt_parts.append("")
        prompt_parts.append("Text:")
        prompt_parts.append(text)

        prompt = "\n".join(prompt_parts)

        resp = _call_llm(prompt, model=self.model)
        if resp is None:
            return text
        return resp.strip() or text

    # ---- Fallback helpers ------------------------------------------

    @staticmethod
    def _fast_cleanup(text: str) -> str:
        """
        Very small heuristic tweaks for when LLM is unavailable.
        """
        if not text:
            return text

        # Remove some common AI boilerplate intros/closings
        boilerplate_phrases = [
            "Here are some ways",
            "In conclusion,",
            "To summarize,",
            "Overall,",
            "In summary,",
            "This section will explore",
        ]
        cleaned = text
        for phrase in boilerplate_phrases:
            cleaned = cleaned.replace(phrase, "")

        # Normalize spacing a bit
        cleaned = "\n".join(line.rstrip() for line in cleaned.splitlines())
        cleaned = textwrap.dedent(cleaned).strip()
        return cleaned


# Convenient singleton instance for simple imports
default_wrapper = HumanizationWrapper()
