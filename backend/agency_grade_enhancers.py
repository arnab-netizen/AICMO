# backend/agency_grade_enhancers.py
from __future__ import annotations

import json
import logging
import os
from typing import Optional

try:
    from openai import OpenAI  # type: ignore
except ImportError:
    OpenAI = None  # type: ignore

logger = logging.getLogger("aicmo.turbo")

# Phase L integration
try:
    from aicmo.memory.engine import augment_prompt_with_memory
except ImportError:
    augment_prompt_with_memory = None  # type: ignore


def _get_openai_client() -> Optional["OpenAI"]:
    """
    Safe helper: returns OpenAI client or None if not available.
    Keeps backend from breaking if deps/env are missing.
    """
    if OpenAI is None:
        return None
    try:
        return OpenAI()
    except Exception:
        return None


def _get_model_name() -> str:
    # Set via env; default to a cheaper mini
    return os.getenv("AICMO_MODEL_MAIN", "gpt-4o-mini")


def _brief_to_text(brief) -> str:
    try:
        return brief.model_dump_json(indent=2)
    except Exception:
        return str(brief)


def _report_to_text(report) -> str:
    try:
        return report.model_dump_json(indent=2)
    except Exception:
        return str(report)


def _call_llm_for_section(
    client: "OpenAI",
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1600,
) -> str:
    """
    Common helper that expects the model to respond with plain markdown/text.
    No JSON parsing to avoid brittle failures.
    """
    try:
        resp = client.chat.completions.create(
            model=_get_model_name(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
        )
        try:
            # Best-effort: first text chunk
            return resp.choices[0].message.content or ""
        except Exception:
            return json.dumps(resp.model_dump(), indent=2)
    except Exception:
        return ""


def _augment_with_phase_l(prompt: str, brief_text: str) -> str:
    """
    Optionally augment a TURBO section prompt with Phase L memory.
    Safe: returns original prompt if Phase L unavailable or empty.

    Args:
        prompt: The user prompt to potentially augment
        brief_text: Client brief text for memory retrieval

    Returns:
        Augmented prompt with learned examples, or original prompt
    """
    if augment_prompt_with_memory is None:
        return prompt

    try:
        # Use Phase L to find similar examples from past reports
        return augment_prompt_with_memory(
            brief_text=brief_text,
            base_prompt=prompt,
            limit=5,  # Include up to 5 relevant examples
        )
    except Exception as e:
        # Non-breaking: if Phase L fails, use original prompt
        logger.debug(f"Phase L augmentation failed (non-critical): {e}")
        return prompt


# =====================================================================
# MAIN ENTRYPOINT – AICMO TURBO
# =====================================================================


def apply_agency_grade_enhancements(brief, report) -> None:
    """
    AICMO TURBO:
    Call once after building a base AICMOOutputReport.
    Adds 'agency-grade' sections into report.extra_sections
    and runs global polishers on those sections.

    Safe:
      - If OpenAI not available or errors → does nothing.
      - Base report remains valid JSON.
      - Phase L memory integration is automatic and non-breaking.
    """
    client = _get_openai_client()
    if client is None:
        return

    brief_text = _brief_to_text(brief)
    report_text = _report_to_text(report)

    # Phase L: Augment brief context with learned examples from past reports
    # This prepends relevant examples to the brief, enriching all TURBO section generation
    brief_text = _augment_with_phase_l(brief_text, brief_text)

    # 1) Outcome forecast
    _add_outcome_forecast_section(client, brief, report, brief_text, report_text)

    # 2) Creative direction / moodboard
    _add_creative_boards_section(client, brief, report, brief_text, report_text)

    # 3) Brand / founder narrative
    _add_brand_story_section(client, brief, report, brief_text, report_text)

    # 4) Budget & media plan
    _add_budget_plan_section(client, brief, report, brief_text, report_text)

    # 5) Creative asset checklist
    _add_asset_checklist_section(client, brief, report, brief_text, report_text)

    # 6) Next 7 days execution checklist
    _add_next_7_days_section(client, brief, report, brief_text, report_text)

    # 7) Competitive positioning matrix
    _add_positioning_matrix_section(client, brief, report, brief_text, report_text)

    # 8) Customer journey map
    _add_journey_map_section(client, brief, report, brief_text, report_text)

    # 9) Messaging matrix
    _add_messaging_matrix_section(client, brief, report, brief_text, report_text)

    # 10) Offer strategy / funnel design
    _add_offer_strategy_section(client, brief, report, brief_text, report_text)

    # 11) Category tension / entry points
    _add_category_tension_section(client, brief, report, brief_text, report_text)

    # 12) Strategic story arcs
    _add_story_arcs_section(client, brief, report, brief_text, report_text)

    # 13) Hero framework
    _add_hero_framework_section(client, brief, report, brief_text, report_text)

    # 14) Maturity-aware focus
    _add_maturity_mode_section(client, brief, report, brief_text, report_text)

    # 15) Multi-channel funnel blueprint
    _add_funnel_blueprint_section(client, brief, report, brief_text, report_text)

    # Global polishers – forbid obvious placeholder phrases
    _strip_placeholders_from_extra_sections(report)


# =====================================================================
# HELPERS
# =====================================================================


def _ensure_extra_sections(report) -> None:
    if not hasattr(report, "extra_sections") or report.extra_sections is None:
        report.extra_sections = {}


# =====================================================================
# SECTION GENERATORS
# =====================================================================


def _add_outcome_forecast_section(client, brief, report, brief_text, report_text):
    _ensure_extra_sections(report)
    system_prompt = (
        "You are a senior performance strategist at a top global agency. "
        "You forecast realistic ranges based on benchmarks – not fake guarantees."
    )
    user_prompt = f"""
Client brief (JSON-like):
{brief_text}

Current draft report (JSON-like):
{report_text}

Write an 'Outcome Forecast – 90 Days' section as markdown.

Rules:
- Use realistic ranges, not guarantees.
- Include: traffic, clicks, leads, demos, conversions (as applicable).
- Mention clear assumptions: budgets, channels, creative quality, sales follow-up.
- Keep it to 4–6 short paragraphs + one simple table.
- Talk like a strategist, not an AI model.
"""
    text = _call_llm_for_section(client, system_prompt, user_prompt)
    if text.strip():
        report.extra_sections["Outcome Forecast – 90 Days"] = text.strip()


def _add_creative_boards_section(client, brief, report, brief_text, report_text):
    _ensure_extra_sections(report)
    system_prompt = (
        "You are a senior creative director. You define visual direction and "
        "storyboards in words, with clarity a designer can execute."
    )
    user_prompt = f"""
Client brief:
{brief_text}

Current draft report:
{report_text}

Write a 'Creative Direction & Moodboard' section as markdown.

Include:
- Overall visual style (colours, composition, typography).
- 3–5 reference moods (e.g. 'clean B2B SaaS dashboards', 'bold neon gradients').
- Sample reel storyboard (3–4 shots).
- Sample carousel structure (slide 1–5).
- Landing page wireframe (sections only, in order).

Do NOT talk about being an AI. Just write the section.
"""
    text = _call_llm_for_section(client, system_prompt, user_prompt)
    if text.strip():
        report.extra_sections["Creative Direction & Moodboard"] = text.strip()


def _add_brand_story_section(client, brief, report, brief_text, report_text):
    _ensure_extra_sections(report)
    system_prompt = (
        "You are a brand strategist. You craft founder and brand narratives "
        "that feel human, specific and emotionally resonant."
    )
    user_prompt = f"""
Given this client:

{brief_text}

And this current plan:

{report_text}

Write a 'Brand & Founder Narrative' section.

Include:
- The brand's role in the category.
- The tension they fight against.
- A simple founder/brand story that can be used on the website, pitch deck, and PR.
- 3 one-liner version options (for bios, intros, social).

Do NOT be generic. Use the industry, audience, and goals.
"""
    text = _call_llm_for_section(client, system_prompt, user_prompt)
    if text.strip():
        report.extra_sections["Brand & Founder Narrative"] = text.strip()


def _add_budget_plan_section(client, brief, report, brief_text, report_text):
    _ensure_extra_sections(report)
    system_prompt = (
        "You are a media planner. You design simple, realistic budget splits "
        "for small to mid-size brands."
    )
    user_prompt = f"""
Brief:
{brief_text}

Plan:
{report_text}

Assume a modest but serious brand: monthly promo budget is in the band they indicated.
Write a 'Budget & Media Plan (Indicative)' section.

Include:
- Suggested monthly budget range (₹ or $; infer from context if possible).
- Split by channel (e.g. LinkedIn, Meta, Google, Influencers, Email).
- What each channel is supposed to achieve.
- 1 simple table summarising the split.

If budget is '0', focus on an organic-first media plan (no fake numbers).
"""
    text = _call_llm_for_section(client, system_prompt, user_prompt)
    if text.strip():
        report.extra_sections["Budget & Media Plan (Indicative)"] = text.strip()


def _add_asset_checklist_section(client, brief, report, brief_text, report_text):
    _ensure_extra_sections(report)
    system_prompt = (
        "You are an account manager at a performance agency. "
        "You give clients brutally clear asset checklists."
    )
    user_prompt = f"""
Using the brief and plan:

{brief_text}

{report_text}

Write a 'Creative Asset Checklist' section.

Include:
- Exact list of assets needed (e.g. 5 LinkedIn posts, 8 reels, 3 landing page variations, 2 email sequences).
- For each asset: purpose, approx length, required inputs from client (logos, testimonials, product shots).
- Write it as a bullet list and a simple table.

This should feel like a working to-do list the client can actually act on.
"""
    text = _call_llm_for_section(client, system_prompt, user_prompt)
    if text.strip():
        report.extra_sections["Creative Asset Checklist"] = text.strip()


def _add_next_7_days_section(client, brief, report, brief_text, report_text):
    _ensure_extra_sections(report)
    system_prompt = (
        "You are an operations-focused strategist. You give precise 7-day "
        "checklists to get a campaign moving."
    )
    user_prompt = f"""
From this brief and plan:

{brief_text}

{report_text}

Write a 'Next 7 Days – Execution Checklist' section.

Structure:
- Day 1–2: setup & alignment
- Day 3–5: asset creation & approvals
- Day 6–7: launch & first optimisation

Make it extremely concrete. Each day should have 3–6 bullet points.
"""
    text = _call_llm_for_section(client, system_prompt, user_prompt)
    if text.strip():
        report.extra_sections["Next 7 Days – Execution Checklist"] = text.strip()


def _add_positioning_matrix_section(client, brief, report, brief_text, report_text):
    _ensure_extra_sections(report)
    system_prompt = (
        "You are a category design consultant. You map brands against each other "
        "in simple matrices (price vs value, complexity vs speed, etc.)."
    )
    user_prompt = f"""
With this client in mind:

{brief_text}

And this strategy:

{report_text}

Write a 'Competitive Positioning Matrix' section.

Include:
- One 2x2 narrative (e.g. 'complex vs simple' and 'generic vs specialised').
- A simple table listing 3–5 competitors + client across key dimensions.

Keep it strategic, not petty.
"""
    text = _call_llm_for_section(client, system_prompt, user_prompt)
    if text.strip():
        report.extra_sections["Competitive Positioning Matrix"] = text.strip()


def _add_journey_map_section(client, brief, report, brief_text, report_text):
    _ensure_extra_sections(report)
    system_prompt = (
        "You are a customer journey designer. You think in stages: Awareness, "
        "Consideration, Decision, Onboarding, Retention."
    )
    user_prompt = f"""
Using the brief and plan:

{brief_text}

{report_text}

Write a 'Customer Journey Map' section.

For each stage (Awareness, Consideration, Decision, Onboarding, Retention):
- Main customer question.
- Brand's job at that stage.
- Example content/asset.
- Primary KPI.

Render as a markdown table + bullet points.
"""
    text = _call_llm_for_section(client, system_prompt, user_prompt)
    if text.strip():
        report.extra_sections["Customer Journey Map"] = text.strip()


def _add_messaging_matrix_section(client, brief, report, brief_text, report_text):
    _ensure_extra_sections(report)
    system_prompt = (
        "You are a messaging strategist. You map audiences to problems, to messages, "
        "to proof, to example lines."
    )
    user_prompt = f"""
From:

{brief_text}

{report_text}

Write a 'Messaging Matrix' section.

Columns:
- Segment
- Core Pain
- Core Promise
- Proof
- Example Line (headline/copy)

Return as a markdown table with 3–5 rows.
"""
    text = _call_llm_for_section(client, system_prompt, user_prompt)
    if text.strip():
        report.extra_sections["Messaging Matrix"] = text.strip()


def _add_offer_strategy_section(client, brief, report, brief_text, report_text):
    _ensure_extra_sections(report)
    system_prompt = (
        "You are a funnel strategist. You design lead magnets, trial offers, "
        "and conversion plays."
    )
    user_prompt = f"""
Given:

{brief_text}

{report_text}

Write an 'Offer Strategy & Funnel Design' section.

Include:
- 1–2 lead magnet ideas.
- 1–2 main offers.
- 1 retargeting/BOFU play.
- Simple funnel diagram in text (Awareness → Lead → Demo → Customer).

This should be practical enough to implement.
"""
    text = _call_llm_for_section(client, system_prompt, user_prompt)
    if text.strip():
        report.extra_sections["Offer Strategy & Funnel Design"] = text.strip()


def _add_category_tension_section(client, brief, report, brief_text, report_text):
    _ensure_extra_sections(report)
    system_prompt = (
        "You are a brand strategist. You define 'the enemy', the core tension, "
        "and the category entry points."
    )
    user_prompt = f"""
Brief:
{brief_text}

Plan:
{report_text}

Write a 'Category Tension & Entry Points' section.

Include:
- The tension the customer feels.
- The 'enemy' (old way, chaos, waste, etc – NOT a competitor).
- 3–5 category entry points (situations when buyer thinks of this category).

Talk in plain language, like a strategist.
"""
    text = _call_llm_for_section(client, system_prompt, user_prompt)
    if text.strip():
        report.extra_sections["Category Tension & Entry Points"] = text.strip()


def _add_story_arcs_section(client, brief, report, brief_text, report_text):
    _ensure_extra_sections(report)
    system_prompt = (
        "You are a content strategist. You build multi-week story arcs, not random posts."
    )
    user_prompt = f"""
Using:

{brief_text}

{report_text}

Write a 'Strategic Story Arcs (4 Weeks)' section.

For 4 weeks:
- Name of arc.
- Core message.
- Example content ideas (3–5 per week).
- Primary KPI.

Keep it tight and implementable.
"""
    text = _call_llm_for_section(client, system_prompt, user_prompt)
    if text.strip():
        report.extra_sections["Strategic Story Arcs (4 Weeks)"] = text.strip()


def _add_hero_framework_section(client, brief, report, brief_text, report_text):
    _ensure_extra_sections(report)
    system_prompt = (
        "You are a narrative strategist. You use hero's journey style structures "
        "for marketing stories."
    )
    user_prompt = f"""
Based on:

{brief_text}

{report_text}

Write a 'Hero Framework' section.

Include:
- The hero (customer).
- The villain (problem/status quo).
- The guide (brand).
- The tool/process.
- The transformation.
- 2–3 example story snippets that could be used in ads/presentations.

Make it feel like a pitch deck slide.
"""
    text = _call_llm_for_section(client, system_prompt, user_prompt)
    if text.strip():
        report.extra_sections["Hero Framework"] = text.strip()


def _add_maturity_mode_section(client, brief, report, brief_text, report_text):
    _ensure_extra_sections(report)
    system_prompt = (
        "You are a growth advisor. You alter strategy based on brand maturity: "
        "early / growth / late."
    )
    user_prompt = f"""
From this brief:

{brief_text}

Guess whether this brand is 'early', 'growth', or 'late' stage.

Write a 'Maturity Mode & Focus' section:

- State the inferred stage.
- Explain what that means for strategy.
- List 3 priorities that matter MOST for that stage.

Keep it pragmatic.
"""
    text = _call_llm_for_section(client, system_prompt, user_prompt)
    if text.strip():
        report.extra_sections["Maturity Mode & Focus"] = text.strip()


def _add_funnel_blueprint_section(client, brief, report, brief_text, report_text):
    _ensure_extra_sections(report)
    system_prompt = (
        "You are a full-funnel strategist. You tie channels to funnel stages "
        "and KPIs in a single view."
    )
    user_prompt = f"""
Given:

{brief_text}

{report_text}

Write a 'Multi-Channel Funnel Blueprint' section.

Include:
- For each stage (TOFU, MOFU, BOFU): which channels, which content, which KPIs.
- Indicate how LinkedIn, email, website/landing pages, and retargeting work together.
- One simple diagram (in text/bullets).

Keep it sharp and B2B/B2C-aware depending on the brief.
"""
    text = _call_llm_for_section(client, system_prompt, user_prompt)
    if text.strip():
        report.extra_sections["Multi-Channel Funnel Blueprint"] = text.strip()


# =====================================================================
# GLOBAL POLISHERS (for turbo sections only)
# =====================================================================


def _strip_placeholders_from_extra_sections(report) -> None:
    """
    Forbid obvious placeholder phrases in Turbo sections.
    """
    _ensure_extra_sections(report)
    forbidden_tokens = [
        "not yet summarised",
        "will be refined later",
        "Not specified",
        "N/A",
        "to be decided",
        "TBD",
    ]

    cleaned = {}
    for title, body in report.extra_sections.items():
        if not isinstance(body, str):
            cleaned[title] = body
            continue
        text = body
        for token in forbidden_tokens:
            text = text.replace(token, "").replace(token.capitalize(), "")
        cleaned[title] = text.strip()

    report.extra_sections = cleaned
