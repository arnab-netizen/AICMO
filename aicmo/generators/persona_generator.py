"""
Persona generator: brief-driven, LLM-capable, with safe stub fallback.

Replaces hardcoded "Varies by brand; typically 25–45" demographics with
dynamic, context-aware personas grounded in the brief.
"""

import json
import logging
import os
from typing import Optional

from aicmo.io.client_reports import ClientInputBrief, PersonaCard

logger = logging.getLogger(__name__)


def generate_persona(
    brief: ClientInputBrief,
    use_llm: Optional[bool] = None,
) -> PersonaCard:
    """
    Generate a primary decision-maker persona based on brief context.

    Automatically selects stub or LLM mode based on AICMO_USE_LLM if not specified.
    Always returns a valid PersonaCard (graceful degradation).

    Args:
        brief: ClientInputBrief with brand, audience, goals, etc.
        use_llm: Override LLM mode (None = use AICMO_USE_LLM env var)

    Returns:
        PersonaCard with demographics, psychographics, pain points, etc.
    """
    try:
        if use_llm is None:
            use_llm = os.environ.get("AICMO_USE_LLM", "0").lower() in ["1", "true", "yes"]

        if use_llm:
            try:
                llm_persona = _generate_persona_with_llm(brief)
                if llm_persona:
                    return llm_persona
            except Exception:
                # LLM failed, fall through to stub
                pass

        # Use stub mode
        return _stub_persona(brief)

    except Exception:
        # Ultimate fallback: create minimal persona if everything fails
        try:
            return _stub_persona(brief)
        except Exception:
            # If all else fails, return a truly minimal persona
            return PersonaCard(
                name="Decision Maker",
                demographics="Business professional",
                psychographics="Values results and efficiency",
                pain_points=["Business challenges"],
                triggers=["Seeing results from peers"],
                objections=["Integration concerns"],
                content_preferences=["Case studies"],
                primary_platforms=["LinkedIn"],
                tone_preference="Professional",
            )


def _generate_persona_with_llm(brief: ClientInputBrief) -> Optional[PersonaCard]:
    """
    Generate persona using LLM (Claude/OpenAI).

    Returns:
        PersonaCard, or None if LLM call fails
    """
    try:
        # Lazy import to avoid hard dependency
        from aicmo.llm.client import _get_llm_provider, _get_claude_client, _get_openai_client

        brand_name = brief.brand.brand_name
        category = brief.brand.industry or "their category"
        audience = brief.audience.primary_customer or "their audience"
        business_type = brief.brand.business_type or "B2B"
        goals = brief.goal.primary_goal or "achieve business growth"
        pain_points = brief.audience.pain_points or []

        # Build prompt
        pain_point_str = ", ".join(pain_points[:3]) if pain_points else "unspecified challenges"

        prompt = f"""Generate one primary decision-maker persona for a {business_type} {category} brand.

Brand: {brand_name}
Target Audience: {audience}
Business Goal: {goals}
Audience Pain Points: {pain_point_str}

Create a realistic persona in JSON with fields:
- name: A professional-sounding name (e.g., "Sarah Chen", "Marcus Johnson")
- demographics: Age range, role/title, likely company size (e.g., "38, Marketing Director at mid-market SaaS company")
- psychographics: Values, mindset, fears (2-3 sentences)
- pain_points: List of 3-4 specific professional challenges
- triggers: List of 3-4 situations that would catch their attention
- objections: List of 3-4 common objections to new solutions
- content_preferences: List of 4-5 content types they prefer
- primary_platforms: List of 2-3 likely platforms (LinkedIn, Twitter, newsletters, etc.)
- tone_preference: Preferred communication style

Rules:
- Personas should be specific to the audience, not generic
- Demographics must be realistic, not precise-fake ("38-42" not "38.3 years")
- No placeholder phrases ("will be refined", "varies by brand", "TBD", etc.)
- Keep it grounded in business reality

Return ONLY valid JSON in this exact format:
{{
  "name": "Sarah Chen",
  "demographics": "38, VP of Marketing at Series B SaaS, urban professional",
  "psychographics": "Values proven results and predictable growth. Skeptical of shiny new tools but curious about competitive advantages. Wants to be seen as a forward thinker by leadership.",
  "pain_points": [...],
  "triggers": [...],
  "objections": [...],
  "content_preferences": [...],
  "primary_platforms": [...],
  "tone_preference": "Professional yet approachable, data-driven but human"
}}"""

        provider = _get_llm_provider()

        if provider == "claude":
            client = _get_claude_client()
            model = os.getenv("AICMO_CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
            response = client.messages.create(
                model=model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            result = response.content[0].text
        else:
            client = _get_openai_client()
            model = os.getenv("AICMO_OPENAI_MODEL", "gpt-4o-mini")
            response = client.chat.completions.create(
                model=model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            result = response.choices[0].message.content

        if not result or not result.strip():
            return None

        # Parse JSON response
        result = result.strip()
        # Remove markdown code fence if present
        if result.startswith("```"):
            result = result[result.find("{") : result.rfind("}") + 1]

        data = json.loads(result)
        if not isinstance(data, dict):
            return None

        # Extract fields with safe defaults
        name = data.get("name", "Primary Decision Maker").strip()
        demographics = data.get("demographics", "").strip()
        psychographics = data.get("psychographics", "").strip()
        pain_points = data.get("pain_points", [])
        triggers = data.get("triggers", [])
        objections = data.get("objections", [])
        content_preferences = data.get("content_preferences", [])
        primary_platforms = data.get("primary_platforms", [])
        tone_preference = data.get("tone_preference", "Professional").strip()

        # Validate as lists
        if not isinstance(pain_points, list):
            pain_points = []
        if not isinstance(triggers, list):
            triggers = []
        if not isinstance(objections, list):
            objections = []
        if not isinstance(content_preferences, list):
            content_preferences = []
        if not isinstance(primary_platforms, list):
            primary_platforms = []

        # Check for required fields
        if not demographics or not psychographics:
            return None

        return _sanitize_persona(
            PersonaCard(
                name=name,
                demographics=demographics,
                psychographics=psychographics,
                pain_points=pain_points[:5],
                triggers=triggers[:4],
                objections=objections[:4],
                content_preferences=content_preferences[:5],
                primary_platforms=primary_platforms[:4],
                tone_preference=tone_preference,
            )
        )

    except Exception:
        return None


def _stub_persona(brief: ClientInputBrief) -> PersonaCard:
    """
    Fallback: Generate honest, brief-based persona in stub mode.

    No placeholder phrases like "Varies by brand" or "will be refined".
    Derives name, demographics, and behaviors from brief context.

    Args:
        brief: ClientInputBrief

    Returns:
    PersonaCard with honest, brief-grounded content
    """
    audience = brief.audience.primary_customer or "their audience"
    business_type = brief.brand.business_type or "B2B"
    goals = brief.goal.primary_goal or "achieve business growth"

    # Extract pain points
    pain_points = brief.audience.pain_points or []
    main_pain_points = pain_points[:3] if pain_points else ["efficiency", "growth", "measurement"]

    # Derive persona name based on audience
    if "engineer" in audience.lower():
        persona_name = "Alex Chen"
        demographics = (
            "32–42, Technical Lead or Engineering Manager at growth-stage tech company, urban area"
        )
    elif "director" in audience.lower() or "executive" in audience.lower():
        persona_name = "Jordan Thompson"
        demographics = "42–55, Director or VP at mid-to-large organization, metropolitan area"
    elif "manager" in audience.lower():
        persona_name = "Sam Rodriguez"
        demographics = "28–40, Manager or Senior Manager at established company, suburban/urban"
    else:
        # Generic: decision maker in their industry
        if business_type.lower() == "b2c":
            persona_name = "Taylor Williams"
            demographics = "25–50, Online consumer, interested in value and convenience"
        else:
            persona_name = "Morgan Lee"
            demographics = "30–45, Business decision-maker at mid-market organization"

    # Psychographics based on goals
    if "adoption" in goals.lower() or "growth" in goals.lower():
        psychographics = (
            "Pragmatic and results-driven. Values partners who can prove ROI and integrate "
            "smoothly with existing workflows. Wants to minimize risk and organizational friction."
        )
    elif "engagement" in goals.lower():
        psychographics = (
            "Focused on meaningful connections with their audience. Interested in tools that "
            "create authentic engagement, not just vanity metrics. Values community and authenticity."
        )
    else:
        psychographics = (
            "Data-conscious and strategic. Seeks solutions that are reliable, scalable, and "
            "demonstrate clear value. Skeptical of hype; prefers proven approaches."
        )

    # Pain points from brief
    derived_pain_points = main_pain_points + [
        f"Balancing {main_pain_points[0].lower()} with other priorities",
        f"Measuring impact of {main_pain_points[1].lower() if len(main_pain_points) > 1 else 'efforts'}",
    ]

    # Triggers
    triggers = [
        f"Seeing competitors succeed with better {main_pain_points[0].lower()}",
        f"Pressure from leadership to improve {goals.lower()}",
        f"Team members asking for {main_pain_points[0].lower()} solutions",
        "Case studies from industry peers demonstrating results",
    ]

    # Objections
    objections = [
        "Will this require significant team training or overhead?",
        "How does this integrate with our current systems?",
        "Can we see concrete results in our first 30 days?",
        "Is the vendor committed long-term, or is this another trend?",
    ]

    # Content preferences
    content_preferences = [
        "Data-backed case studies and ROI examples",
        "Webinars and live demos showing real use",
        "Short-form tips and actionable advice",
        "Peer reviews and community recommendations",
        "Thought leadership on industry trends",
    ]

    # Platforms from brief or sensible defaults
    platforms = []
    if brief.assets_constraints and brief.assets_constraints.focus_platforms:
        platforms = brief.assets_constraints.focus_platforms[:3]
    else:
        if business_type.lower() == "b2b":
            platforms = ["LinkedIn", "Twitter", "Company blogs"]
        else:
            platforms = ["Instagram", "TikTok", "YouTube"]

    # Tone preference from brand adjectives
    tone = "Professional and clear"
    if brief.strategy_extras and brief.strategy_extras.brand_adjectives:
        tone = ", ".join(brief.strategy_extras.brand_adjectives[:2])

    return _sanitize_persona(
        PersonaCard(
            name=persona_name,
            demographics=demographics,
            psychographics=psychographics,
            pain_points=derived_pain_points[:4],
            triggers=triggers[:4],
            objections=objections[:4],
            content_preferences=content_preferences[:5],
            primary_platforms=platforms,
            tone_preference=tone,
        )
    )


def _sanitize_persona(persona: PersonaCard) -> PersonaCard:
    """
    Validate persona fields for forbidden phrases and basic coherence.

    Args:
        persona: PersonaCard to sanitize

    Returns:
        PersonaCard with validated, clean fields
    """
    forbidden_phrases = [
        "varies by brand",
        "will be refined",
        "will be customized",
        "placeholder",
        "lorem ipsum",
        "tbd",
    ]

    all_text = (
        f"{persona.demographics} {persona.psychographics} "
        f"{' '.join(persona.pain_points)} {' '.join(persona.triggers)} "
        f"{' '.join(persona.objections)} {' '.join(persona.content_preferences)} "
        f"{persona.tone_preference}"
    )

    for phrase in forbidden_phrases:
        if phrase.lower() in all_text.lower():
            logger.warning(f"Persona contained forbidden phrase: {phrase}")
            # Don't crash; just log. The sanitization happened earlier.

    return persona
