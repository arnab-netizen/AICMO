"""LLM enhancement layer for AICMO output – supports Claude Sonnet 4 (default) and OpenAI."""

from __future__ import annotations

import os
from typing import Any, Optional, Literal

from aicmo.io.client_reports import ClientInputBrief, AICMOOutputReport


def _get_llm_provider() -> Literal["claude", "openai"]:
    """Determine which LLM provider to use based on environment variables."""
    # Default to Claude Sonnet 4 if available, fall back to OpenAI
    provider = os.getenv("AICMO_LLM_PROVIDER", "claude").lower()
    if provider not in ("claude", "openai"):
        provider = "claude"
    return provider  # type: ignore


def _get_claude_client():
    """
    Lazy import of Anthropic SDK for Claude models.
    """
    try:
        from anthropic import Anthropic  # type: ignore
    except ImportError as e:  # pragma: no cover - handled gracefully by caller
        raise RuntimeError(
            "Anthropic SDK is not installed. Install `anthropic` and try again."
        ) from e

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        return Anthropic(api_key=api_key)
    return Anthropic()


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
    provider: Literal["claude", "openai"] = "claude",
) -> str:
    """
    Ask the LLM to refine / polish a single text block.

    If anything goes wrong, returns the original text unchanged.
    Supports both Claude (via Anthropic) and OpenAI APIs.
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

        if provider == "claude":
            # Use Anthropic Claude API
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system="You are a senior marketing strategist helping refine marketing copy.",
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )
            new_text = response.content[0].text
        else:
            # Use OpenAI API
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

    Default: Claude Sonnet 4 (via ANTHROPIC_API_KEY)
    Fallback: OpenAI (via OPENAI_API_KEY and AICMO_OPENAI_MODEL)
    
    If LLM is not configured, returns stub_output unchanged with a warning.
    """
    from aicmo.core.llm.runtime import llm_enabled, safe_llm_status
    
    # Graceful degradation: if LLM not enabled, return stub output
    if not llm_enabled():
        status = safe_llm_status()
        # Log warning but don't crash
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"LLM not enabled ({status['reason']}). Returning stub output unchanged.")
        return stub_output
    
    options = options or {}

    # Determine provider and get appropriate client + model
    provider = _get_llm_provider()

    if provider == "claude":
        client = _get_claude_client()
        # Default to Claude Sonnet 4 (latest recommended Claude 3 model)
        model = os.getenv("AICMO_CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    else:
        client = _get_openai_client()
        model = os.getenv("AICMO_OPENAI_MODEL", "gpt-4o-mini")

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
        provider=provider,
    )
    mp.situation_analysis = _rewrite_text_block(
        client,
        model,
        brief_json,
        "Marketing plan – Situation analysis",
        mp.situation_analysis,
        provider=provider,
    )
    mp.strategy = _rewrite_text_block(
        client,
        model,
        brief_json,
        "Marketing plan – Strategy",
        mp.strategy,
        provider=provider,
    )

    # --- Campaign big idea ---
    cb = enhanced.campaign_blueprint
    cb.big_idea = _rewrite_text_block(
        client,
        model,
        brief_json,
        "Campaign big idea",
        cb.big_idea,
        provider=provider,
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
                        provider=provider,
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
                        provider=provider,
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
                        provider=provider,
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
                    provider=provider,
                )
                # ^ small polish: this keeps it per-platform
                new_caption = _rewrite_text_block(
                    client,
                    model,
                    brief_json,
                    f"{v.platform} caption",
                    v.caption,
                    max_tokens=220,
                    provider=provider,
                )
                v.hook = new_hook
                v.caption = new_caption
                new_variants.append(v)
            cr.channel_variants = new_variants

    return enhanced
