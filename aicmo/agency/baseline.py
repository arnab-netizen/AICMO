"""
Agency Baseline – Hardwired Agency-Grade Pipeline

This module provides two main entry points:
1. apply_agency_baseline() – Full strategy report pipeline (14 sections)
2. apply_quick_social_baseline() – Quick social/calendar pipeline (9 sections)

Both pipelines scaffold, deepen, enforce narrative, inject KPIs, humanize, and render
using WOW templates. They guarantee agency-grade structure even if raw LLM output is messy.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, Optional

from aicmo.presets.wow_templates import WOW_TEMPLATES

LLMFunc = Callable[[str, str], str]
Context = Dict[str, Any]


# ==========================
# Strategy Report Baseline
# ==========================


def apply_agency_baseline(
    brief: Context,
    raw_draft: str,
    llm: LLMFunc,
    pack_key: Optional[str] = None,
) -> str:
    """
    Layer One – Hardwired Agency Mode.

    Pipeline:
      1. Scaffold into agency-grade structure (14 sections)
      2. Enforce minimum strategic depth
      3. Enforce narrative cohesion
      4. Inject KPIs & business logic
      5. Humanize + QA
      6. Render into WOW template (agency_strategy_default by default)
    """
    scaffolded = _scaffold_to_agency_structure(brief, raw_draft, llm)
    deepened = _enforce_min_depth(brief, scaffolded, llm)
    narrated = _enforce_narrative_cohesion(brief, deepened, llm)
    measured = _inject_kpis_and_logic(brief, narrated, llm)
    humanized = _humanize_and_qa(brief, measured, llm)

    template_key = pack_key
    template = WOW_TEMPLATES.get(template_key)
    if not template:
        return ""  # No WOW template defined for this package
    rendered = _render_wow_template(template, brief, humanized)

    return rendered


def _scaffold_to_agency_structure(brief: Context, draft: str, llm: LLMFunc) -> str:
    """Scaffold messy input into clean 14-section structure."""
    system = (
        "You are a strategy director at a top-tier marketing agency. "
        "You always think in decks, not loose text. You will take a messy internal draft "
        "and turn it into a clean, sectioned strategy report."
    )

    user = f"""
You are given:

1) CLIENT BRIEF (structured, may be partial):
{brief}

2) RAW INTERNAL DRAFT (may be shallow, repetitive or incomplete):
{draft}

Task:
- Rewrite the content into the following EXACT section structure.
- If some sections are missing in the draft, intelligently fill them based on the brief and standard agency practice.
- Do NOT invent fake hard numbers or fabricated case-study details; it's okay to stay qualitative where data is unknown.
- Keep section headings EXACTLY as written below.

REQUIRED STRUCTURE:

1. Executive Summary
2. Brand & Market Context
3. Problem / Challenge Definition
4. Audience & Key Insight
5. Brand Positioning & Strategic Platform
6. Competitive & Market Landscape
7. Big Idea & Strategic Pillars
8. Messaging Architecture
9. Channel & Content Strategy
10. Phasing & Roadmap
11. Measurement & KPIs
12. Budget & Investment Logic
13. Risks, Assumptions & Dependencies
14. Implementation Plan & Next Steps

Return ONLY the structured report with these headings.
"""

    return llm(system, user)


def _enforce_min_depth(brief: Context, structured: str, llm: LLMFunc) -> str:
    """Ensure each section meets minimum depth requirements."""
    system = (
        "You are a senior strategist. Your job is to enforce minimum strategic depth "
        "on an already structured report. You must avoid shallow, one-line sections."
    )

    user = f"""
You are given a structured report that already follows this structure:

1. Executive Summary
2. Brand & Market Context
3. Problem / Challenge Definition
4. Audience & Key Insight
5. Brand Positioning & Strategic Platform
6. Competitive & Market Landscape
7. Big Idea & Strategic Pillars
8. Messaging Architecture
9. Channel & Content Strategy
10. Phasing & Roadmap
11. Measurement & KPIs
12. Budget & Investment Logic
13. Risks, Assumptions & Dependencies
14. Implementation Plan & Next Steps

REPORT:
{structured}

Depth Rules (minimums):
- Executive Summary: at least 3 concise bullets (challenge, key moves, expected impact).
- Audience & Key Insight: at least 2 audience segments or sub-groups, plus 1 explicit human tension/insight.
- Competitive & Market Landscape: at least 3 competitor archetypes or patterns (even if anonymised).
- Big Idea & Strategic Pillars: 1 clearly named Big Idea + 3–5 strategic pillars.
- Channel & Content Strategy: each primary channel has a role, objectives, and 2–3 example tactics or content ideas.
- Measurement & KPIs: at least 1 primary KPI per main objective.
- Implementation Plan & Next Steps: at least 5 concrete next steps with clear owner/time horizon where possible.

Tasks:
- Expand sections that do not meet these depth rules.
- Keep the structure and headings unchanged.
- Do not add made-up statistics or fabricated data; it's okay to use qualitative KPIs (e.g. 'healthy engagement rate') when you lack numbers.

Return the full, expanded report.
"""

    return llm(system, user)


def _enforce_narrative_cohesion(brief: Context, deepened: str, llm: LLMFunc) -> str:
    """Ensure all sections ladder up to one clear story."""
    system = (
        "You are a narrative-led strategy director. You ensure that every section of a strategy deck ladders up "
        "to one clear story: context → tension → big idea → plan → impact."
    )

    user = f"""
You are given:

BRIEF:
{brief}

DEEPENED REPORT:
{deepened}

Tasks:
- Identify the core narrative in one short paragraph: context, key tension, big idea, intended impact.
- Ensure that the same big idea and key tension are consistently referenced across:
  - Brand Positioning & Strategic Platform
  - Big Idea & Strategic Pillars
  - Messaging Architecture
  - Channel & Content Strategy
  - Phasing & Roadmap
- Add short connective sentences where needed so the report clearly reads like ONE joined-up story.
- Remove or rephrase any content that contradicts the central idea or target audience.

Return the full report with improved narrative cohesion and an explicit mention of the core big idea in all relevant sections.
"""

    return llm(system, user)


def _inject_kpis_and_logic(brief: Context, narrated: str, llm: LLMFunc) -> str:
    """Tie strategy to measurable outcomes and business logic."""
    system = (
        "You are a performance-oriented strategist. You tie strategy to measurable outcomes "
        "and basic business logic without fabricating data."
    )

    user = f"""
You are given:

BRIEF:
{brief}

REPORT (already structured and narratively coherent):
{narrated}

Tasks:
- For each business/marketing objective, ensure there is at least one primary KPI and, where sensible, a supporting metric.
- Map:
  - Awareness objectives → reach, impressions, video views, engagement rate.
  - Consideration objectives → clicks, CTR, time on site, add-to-cart, saves.
  - Conversion objectives → leads, purchases, revenue, ROAS where appropriate.
- Add a short description of:
  - How measurement will happen (tools or platforms).
  - Reporting cadence (weekly, monthly, post-campaign review).
- Ensure the 'Budget & Investment Logic' section includes a rationale for the suggested split (e.g. why lean into IG vs Google for this brief).

Important:
- Do NOT invent specific numeric results or fake brand names.
- You can use qualitative language like 'healthy engagement rate' or 'target ROAS range' without stating fake hard numbers.

Return the full report with KPIs and business logic strengthened.
"""

    return llm(system, user)


def _humanize_and_qa(brief: Context, measured: str, llm: LLMFunc) -> str:
    """Final polish: remove AI tells, enforce premium language, run QA checklist."""
    system = (
        "You are a senior strategist doing a final client-ready polish. "
        "You remove AI tells, enforce premium but human language, and run a strict quality checklist."
    )

    user = f"""
You are given the near-final report below:

BRIEF:
{brief}

REPORT:
{measured}

Language & Tone Rules:
- Confident, direct, human. Avoid hedging and robotic phrasing.
- Avoid banned phrases: 'As an AI language model', 'In conclusion', 'This report will discuss', and generic filler.
- Limit empty buzzwords: only use terms like 'world-class', 'cutting-edge' or 'next-generation' if really justified.
- Prefer specific, concrete language over vague statements.

Quality Checklist (ensure all before returning):
1. Are all 14 sections present and clearly labelled?
2. Is the business problem defined beyond 'increase visibility'?
3. Is the audience described beyond age/gender (behaviours, motivations, barriers)?
4. Is there one clearly named big idea/platform?
5. Do channels have roles and KPIs, not just names?
6. Are there at least a few concrete content or creative examples?
7. Are KPIs reasonably mapped to objectives without fabricating numbers?
8. Is language free of obvious AI tells and repetitive phrasing?
9. Is there a clear set of next steps that a client could act on in the next 0–2 weeks?

If any checklist item fails, quietly fix the report and then return the improved version.

Return ONLY the final, polished, client-ready report.
"""

    return llm(system, user)


# ==========================
# Quick Social / Calendar Baseline
# ==========================


def apply_quick_social_baseline(
    brief: Context,
    raw_draft: str,
    llm: LLMFunc,
    pack_key: Optional[str] = None,
) -> str:
    """
    Lighter Layer One – Hardwired Agency Mode for quick social / calendars.

    Pipeline:
      1. Scaffold into a compact social-content structure (9 sections)
      2. Enrich with pillars, hooks, calendar outline, hashtags & CTAs
      3. Humanize + QA for social tone
      4. Render into quick_social WOW template
    """
    scaffolded = _qs_scaffold_to_social_structure(brief, raw_draft, llm)
    enriched = _qs_enrich_calendar_and_hooks(brief, scaffolded, llm)
    humanized = _qs_humanize_and_qa(brief, enriched, llm)

    template_key = pack_key
    template = WOW_TEMPLATES.get(template_key)
    if not template:
        return ""  # No WOW template defined for this package
    rendered = _render_wow_template(template, brief, humanized)

    return rendered


def _qs_scaffold_to_social_structure(brief: Context, draft: str, llm: LLMFunc) -> str:
    """Scaffold messy input into clean 9-section social structure."""
    system = (
        "You are a social-first content strategist at a top agency. "
        "You specialise in turning messy inputs into clean, actionable social plans."
    )

    user = f"""
You are given:

1) BRIEF (may be partial):
{brief}

2) RAW DRAFT (may be shallow, repetitive, or not structured):
{draft}

Task:
Reshape and rewrite this into a compact social content plan with the following structure:

1. Snapshot & Objectives
2. Audience Snapshot
3. Content Pillars & Creative Angles
4. Posting Rhythm & Format Mix
5. 30-Day Content Calendar (Outline)
6. Hooks, Captions & Hashtag Directions
7. CTAs & Funnel Logic
8. Measurement & Quick Optimization
9. Next Steps (0–2 Weeks)

Notes:
- '30-Day Content Calendar (Outline)' can be a markdown table (Day / Theme / Format / Hook / CTA) or a bullet list per week.
- If the draft doesn't contain a full calendar, intelligently construct one from the brief.
- Do NOT fabricate specific performance numbers; you can keep benchmarks qualitative.

Return ONLY the plan with these headings.
"""

    return llm(system, user)


def _qs_enrich_calendar_and_hooks(brief: Context, structured: str, llm: LLMFunc) -> str:
    """Enrich social plan with varied calendar, hooks, and CTAs."""
    system = (
        "You are a creative social strategist. "
        "Your job is to make the plan feel scroll-stopping, varied, and practical."
    )

    user = f"""
You are given a structured social plan:

BRIEF:
{brief}

STRUCTURED PLAN:
{structured}

Tasks:
- Strengthen 'Content Pillars & Creative Angles':
  - Make sure there are at least 3–5 clear pillars (e.g. education, social proof, offers, BTS, culture).
  - For each pillar, add 2–3 example angles or storylines.
- Strengthen '30-Day Content Calendar (Outline)':
  - Ensure there is a clear sense of variety across the 30 days (formats, topics, pillar mix).
  - Each day (or content slot) should have at least:
    - A theme or idea.
    - A suggested format (Reel, static, Story, carousel, etc.).
    - A hook angle in 5–10 words.
- Strengthen 'Hooks, Captions & Hashtag Directions':
  - Add at least 8–12 example hook lines suited to the brand and audience.
  - Add simple caption guidance (e.g. start with a hook, add value, close with CTA).
  - Add a hashtag strategy (e.g. % split across branded / niche / broad tags) + a few example tag clusters.
- Ensure CTAs and funnel logic show how social leads to:
  - DMs, clicks, leads, or purchases depending on the brief.

Constraints:
- No fabricated metrics or claims; keep performance language qualitative if needed.
- Keep the tone energetic but not cringe; avoid overused social clichés as much as possible.

Return the full enriched plan.
"""

    return llm(system, user)


def _qs_humanize_and_qa(brief: Context, enriched: str, llm: LLMFunc) -> str:
    """Polish social plan: energetic, punchy, human, client-ready."""
    system = (
        "You are doing the final polish on a social content plan. "
        "You ensure it's human, punchy, and client-ready."
    )

    user = f"""
You are given the enriched quick social plan:

BRIEF:
{brief}

PLAN:
{enriched}

Language & Tone Rules:
- Clear, energetic, but not childish.
- Avoid generic AI-sounding phrases like 'In conclusion', 'This document will cover', or 'As an AI'.
- Avoid generic social clichés where possible ('crush your goals', 'go viral', etc.).
- Use concise, concrete language that a busy founder or marketing manager can understand at a glance.

Checklist:
1. Are all sections present and clearly labelled?
2. Does the 'Snapshot & Objectives' clearly state the main goal for social?
3. Does the 'Audience Snapshot' go beyond age/gender (behaviours, motivations, frictions)?
4. Are there at least 3–5 distinct content pillars?
5. Does the 30-Day Calendar feel varied and realistic for the brand?
6. Are there multiple example hooks and clear caption/hashtag guidance?
7. Are CTAs and funnel logic connected to plausible next steps (DMs, clicks, etc.)?
8. Are KPIs and optimization points mentioned without faking specific numbers?
9. Is the overall tone confident, human, and free of obvious AI tells?

If anything fails the checklist, quietly fix it and then return ONLY the final, polished plan.
"""

    return llm(system, user)


# ==========================
# WOW Template Rendering (Shared)
# ==========================


def _render_wow_template(template: str, brief: Context, full_report_text: str) -> str:
    """
    Simple double-curly placeholder renderer using brief context.

    - Uses brief keys where available.
    - Falls back to sensible defaults or extracts bits from the report when missing.
    - Does NOT try to be a full templating engine – just enough to keep things safe.
    """

    # Prepare a flat string context from the brief + a few generic fallbacks.
    ctx: Dict[str, str] = {}

    def _get(key: str, default: str = "") -> str:
        val = brief.get(key) if isinstance(brief, dict) else None
        if val is None:
            return default
        if isinstance(val, (list, tuple)):
            return ", ".join(str(v) for v in val)
        return str(val)

    ctx.update(
        {
            "brand_name": _get("brand_name", _get("client_name", "The Brand")),
            "campaign_name": _get(
                "campaign_name",
                _get("campaign_title", "Marketing & Campaign Plan"),
            ),
            "primary_market": _get(
                "primary_market",
                _get("city", _get("market", "Target Market")),
            ),
            "timeframe": _get("timeframe", _get("duration", "Campaign Period")),
            "primary_channel": _get("primary_channel", "Social Media"),
            "secondary_channels": _get("secondary_channels", ""),
            "campaign_theme": _get("campaign_theme", ""),
            "core_challenge": _get("core_challenge", ""),
            "big_idea": _get("big_idea", ""),
            "primary_objectives": _get("primary_objectives", ""),
            "expected_impact": _get("expected_impact", ""),
            "category": _get("category", ""),
            "brand_role": _get("brand_role", ""),
            "perception_shift": _get("perception_shift", ""),
            "market_dynamics": _get("market_dynamics", ""),
            "business_problem": _get("business_problem", ""),
            "why_now": _get("why_now", ""),
            "underlying_causes": _get("underlying_causes", ""),
            "audience_segments": _get("audience_segments", ""),
            "audience_behaviours": _get("audience_behaviours", ""),
            "audience_occasions": _get("audience_occasions", ""),
            "audience_short": _get("audience_short", _get("target_audience", "")),
            "audience_needs": _get("audience_needs", ""),
            "audience_barriers": _get("audience_barriers", ""),
            "key_insight": _get("key_insight", ""),
            "brand_promise": _get("brand_promise", ""),
            "proof_points": _get("proof_points", ""),
            "tone_personality": _get("tone_personality", ""),
            "social_tone": _get("social_tone", _get("tone_personality", "")),
            "strategic_platform": _get("strategic_platform", ""),
            "competitor_archetypes": _get("competitor_archetypes", ""),
            "competitor_patterns": _get("competitor_patterns", ""),
            "whitespace_opportunity": _get("whitespace_opportunity", ""),
            "big_idea_name": _get("big_idea_name", ""),
            "big_idea_summary": _get("big_idea_summary", ""),
            "strategic_pillars": _get("strategic_pillars", ""),
            "core_message": _get("core_message", ""),
            "support_messages": _get("support_messages", ""),
            "audience_specific_messages": _get("audience_specific_messages", ""),
            "funnel_messages": _get("funnel_messages", ""),
            "channel_roles": _get("channel_roles", ""),
            "channel_tactics": _get("channel_tactics", ""),
            "content_pillars": _get("content_pillars", ""),
            "content_angles": _get("content_angles", ""),
            "creative_examples": _get("creative_examples", ""),
            "phasing_overview": _get("phasing_overview", ""),
            "roadmap_30_60_90": _get("roadmap_30_60_90", ""),
            "key_milestones": _get("key_milestones", ""),
            "objectives_kpis": _get("objectives_kpis", ""),
            "channel_kpis": _get("channel_kpis", ""),
            "measurement_stack": _get("measurement_stack", ""),
            "reporting_cadence": _get("reporting_cadence", ""),
            "budget_split": _get("budget_split", ""),
            "budget_rationale": _get("budget_rationale", ""),
            "budget_scenarios": _get("budget_scenarios", ""),
            "risks_mitigations": _get("risks_mitigations", ""),
            "critical_assumptions": _get("critical_assumptions", ""),
            "dependencies": _get("dependencies", ""),
            "next_steps_immediate": _get("next_steps_immediate", ""),
            "owner_matrix": _get("owner_matrix", ""),
            "success_90_days": _get("success_90_days", ""),
            "social_objectives": _get("social_objectives", _get("primary_objectives", "")),
            "posting_frequency": _get("posting_frequency", "Daily"),
            "format_mix": _get("format_mix", "Reels, Posts, Stories"),
            "weekly_cadence": _get("weekly_cadence", ""),
            "calendar_outline": _get("calendar_outline", ""),
            "sample_hooks": _get("sample_hooks", ""),
            "caption_directions": _get("caption_directions", ""),
            "hashtag_strategy": _get("hashtag_strategy", ""),
            "primary_ctas": _get("primary_ctas", ""),
            "cta_mix": _get("cta_mix", ""),
            "funnel_connection": _get("funnel_connection", ""),
            "social_kpis": _get("social_kpis", ""),
            "social_benchmarks": _get("social_benchmarks", ""),
            "weekly_review_ritual": _get("weekly_review_ritual", ""),
            "setup_checklist": _get("setup_checklist", ""),
            "owners_summary": _get("owners_summary", ""),
        }
    )

    def replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1).strip()
        return ctx.get(key, "")

    return re.sub(r"{{\s*([^}]+)\s*}}", replace, template)
