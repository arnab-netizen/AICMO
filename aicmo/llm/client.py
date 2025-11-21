"""LLM enhancement layer for AICMO output – optional OpenAI polish layer."""

from __future__ import annotations

import os
from typing import Any, Optional

from aicmo.io.client_reports import ClientInputBrief, AICMOOutputReport


def _get_openai_client():
    """
    Lazy import of OpenAI so tests (and users without the SDK installed)
    can still run as long as LLM mode is disabled.
    """
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as e:  # pragma: no cover - handled gracefully by caller
        raise RuntimeError("OpenAI SDK is not installed. Install `openai` and try again.") from e

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return OpenAI(api_key=api_key)
    return OpenAI()


def _rewrite_text_block(
    client: Any,
    model: str,
    brief_json: str,
    section_label: str,
    original_text: str,
    max_tokens: int = 600,
) -> str:
    """
    Ask the LLM to refine / polish a single text block.

    If anything goes wrong, returns the original text unchanged.
    """
    if not original_text or not original_text.strip():
        return original_text

    try:
        prompt = f"""
You are a senior marketing strategist.

You are helping refine one section of a client deliverable.

[SECTION]: {section_label}

[BRIEF JSON]:
{brief_json}

[CURRENT TEXT]:
{original_text}

Rewrite ONLY this section so that it is:
- clearer
- more compelling
- specific to the brand and goals
- written in simple business English

IMPORTANT:
- Keep the structure (paragraph count) roughly similar.
- Do NOT add new sections or headings.
- Output ONLY the rewritten text, no explanations.
""".strip()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior marketing strategist helping refine marketing copy.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        new_text = response.choices[0].message.content
        if not new_text:
            return original_text
        return str(new_text).strip()
    except Exception:
        # Fallback: never break the flow if the LLM call fails
        return original_text


def enhance_with_llm(
    brief: ClientInputBrief,
    stub_output: AICMOOutputReport,
    options: Optional[dict[str, Any]] = None,
) -> AICMOOutputReport:
    """
    Take the deterministic stub output and let the LLM
    'polish' key text sections.

    This keeps structure stable (good for tests / CI)
    while upgrading the actual copy for real clients.
    """
    options = options or {}
    # 👉 Set this env var to your mini model id (e.g. gpt-4o-mini)
    model = os.getenv("AICMO_OPENAI_MODEL", "gpt-4o-mini")

    client = _get_openai_client()
    brief_json = brief.model_dump_json(indent=2)

    enhanced = stub_output.model_copy(deep=True)

    # --- Marketing plan sections ---
    mp = enhanced.marketing_plan
    mp.executive_summary = _rewrite_text_block(
        client,
        model,
        brief_json,
        "Marketing plan – Executive summary",
        mp.executive_summary,
    )
    mp.situation_analysis = _rewrite_text_block(
        client,
        model,
        brief_json,
        "Marketing plan – Situation analysis",
        mp.situation_analysis,
    )
    mp.strategy = _rewrite_text_block(
        client,
        model,
        brief_json,
        "Marketing plan – Strategy",
        mp.strategy,
    )

    # --- Campaign big idea ---
    cb = enhanced.campaign_blueprint
    cb.big_idea = _rewrite_text_block(
        client,
        model,
        brief_json,
        "Campaign big idea",
        cb.big_idea,
    )

    # --- Creatives: hooks, captions, email subjects, channel captions ---
    cr = enhanced.creatives
    if cr is not None:
        if getattr(cr, "hooks", None):
            new_hooks = []
            for h in cr.hooks:
                new_hooks.append(
                    _rewrite_text_block(
                        client,
                        model,
                        brief_json,
                        "Short hook line",
                        h,
                        max_tokens=120,
                    )
                )
            cr.hooks = new_hooks

        if getattr(cr, "captions", None):
            new_caps = []
            for c in cr.captions:
                new_caps.append(
                    _rewrite_text_block(
                        client,
                        model,
                        brief_json,
                        "Social media caption",
                        c,
                        max_tokens=200,
                    )
                )
            cr.captions = new_caps

        if getattr(cr, "email_subject_lines", None):
            new_subjects = []
            for s in cr.email_subject_lines:
                new_subjects.append(
                    _rewrite_text_block(
                        client,
                        model,
                        brief_json,
                        "Email subject line (keep super short)",
                        s,
                        max_tokens=40,
                    )
                )
            cr.email_subject_lines = new_subjects

        if getattr(cr, "channel_variants", None):
            new_variants = []
            for v in cr.channel_variants:
                new_hook = _rewrite_text_block(
                    client,
                    model,
                    brief_json,
                    f"{v.platform} hook",
                    v.hook,
                    max_tokens=80,
                )
                # ^ small polish: this keeps it per-platform
                new_caption = _rewrite_text_block(
                    client,
                    model,
                    brief_json,
                    f"{v.platform} caption",
                    v.caption,
                    max_tokens=220,
                )
                v.hook = new_hook
                v.caption = new_caption
                new_variants.append(v)
            cr.channel_variants = new_variants

    return enhanced
