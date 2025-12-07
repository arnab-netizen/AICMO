"""
Brand Strategy Block Generator - structured LLM generation for brand strategy components.

Generates comprehensive brand strategy data including positioning, cultural tension,
brand archetypes, messaging hierarchy, and brand story using LLM with JSON validation.
"""

import json
import logging
from typing import Dict, Any

from backend.models_brand_strategy import (
    BrandPositioning,
    CulturalTension,
    BrandArchetype,
    MessagingHierarchy,
    MessagingPillar,
    BrandStory,
)
from backend.dependencies import get_llm

logger = logging.getLogger(__name__)


def generate_brand_strategy_block(brief: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate structured brand strategy data using LLM.

    Args:
        brief: Dictionary with keys:
            - brand_name: Name of the brand
            - industry: Industry/market
            - product_service: Product or service offered
            - primary_customer: Primary target customer
            - pain_points: List of customer pain points
            - objectives: Brand/campaign objectives
            - business_type: Type of business (B2B, B2C, etc.)

    Returns:
        Dict with keys: positioning, cultural_tension, brand_archetype,
        messaging_hierarchy, brand_story
    """
    try:
        llm = get_llm()
    except Exception:
        # If LLM unavailable (no API key, offline), use deterministic fallback
        return _generate_fallback_strategy(brief)

    # Extract brief fields with fallbacks
    brand_name = brief.get("brand_name", "Your Brand")
    industry = brief.get("industry", "your industry")
    product_service = brief.get("product_service", "solutions")
    primary_customer = brief.get("primary_customer", "target customers")
    pain_points = brief.get("pain_points", [])
    objectives = brief.get("objectives", "growth")
    business_type = brief.get("business_type", "")

    pain_points_text = "; ".join(pain_points) if pain_points else "operational challenges"

    # Build the LLM prompt with explicit JSON structure requirements
    prompt = f"""You are a senior brand strategist. Generate comprehensive brand strategy as a JSON object with this exact structure:

{{
  "positioning": {{
    "category": "...",
    "target_audience": "...",
    "competitive_whitespace": "...",
    "benefit_statement": "...",
    "reason_to_believe": "..."
  }},
  "cultural_tension": {{
    "tension_statement": "...",
    "this_brand_believes": "...",
    "how_we_resolve_it": "..."
  }},
  "brand_archetype": {{
    "primary": "...",
    "secondary": "...",
    "description": "...",
    "on_brand_behaviours": ["...", "...", "..."],
    "off_brand_behaviours": ["...", "...", "..."]
  }},
  "messaging_hierarchy": {{
    "brand_promise": "...",
    "pillars": [
      {{"name": "...", "description": "...", "rtbs": ["...", "..."]}},
      {{"name": "...", "description": "...", "rtbs": ["...", "..."]}},
      {{"name": "...", "description": "...", "rtbs": ["...", "..."]}}
    ]
  }},
  "brand_story": {{
    "hero": "...",
    "conflict": "...",
    "resolution": "...",
    "what_future_looks_like": "..."
  }}
}}

BRAND CONTEXT:
- Brand Name: {brand_name}
- Industry: {industry}
- Business Type: {business_type}
- Product/Service: {product_service}
- Primary Customer: {primary_customer}
- Customer Pain Points: {pain_points_text}
- Objectives: {objectives}

REQUIREMENTS:

1. POSITIONING:
   - category: The market category {brand_name} competes in
   - target_audience: Specific description of who they serve
   - competitive_whitespace: The unoccupied space {brand_name} owns
   - benefit_statement: Core benefit to customers
   - reason_to_believe: Why customers trust this brand

2. CULTURAL TENSION:
   - tension_statement: A cultural or social tension the brand addresses
   - this_brand_believes: {brand_name}'s belief about the tension
   - how_we_resolve_it: How {brand_name} solves the tension through its product/service

3. BRAND ARCHETYPE (Choose primary from: Hero, Sage, Creator, Innovator, Explorer, Innocent, Everyman, Lover, Jester, Magician, Ruler, Caregiver):
   - primary: Main archetype (e.g., Hero, Creator)
   - secondary: Supporting archetype
   - description: 1-2 sentences explaining the archetype combination
   - on_brand_behaviours: 3 specific examples of how brand lives this archetype
   - off_brand_behaviours: 3 examples of what contradicts the archetype

4. MESSAGING HIERARCHY:
   - brand_promise: The core promise {brand_name} makes (1 sentence)
   - pillars: EXACTLY 3 pillars with:
     * name: Pillar title (short)
     * description: 1-2 sentence explanation
     * rtbs: 2-3 reasons to believe supporting this pillar

5. BRAND STORY:
   - hero: The protagonist (customer persona or type)
   - conflict: The obstacle the hero faces
   - resolution: How {brand_name} helps overcome the conflict
   - what_future_looks_like: The transformed future state

TONE: Professional, authoritative, specific to {brand_name}'s industry and positioning. Avoid generic statements.

RETURN ONLY VALID JSON - no markdown, no extra text."""

    try:
        # Call LLM requesting JSON
        response_text = llm.generate(
            prompt,
            temperature=0.7,
            max_tokens=2500,
            response_format="json" if hasattr(llm, "response_format") else None,
        )

        # Parse JSON response
        if isinstance(response_text, str):
            # Clean up response if needed
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            try:
                response_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM JSON response: {e}. Using fallbacks.")
                response_data = {}
        else:
            response_data = response_text

        # Validate and fill with fallbacks
        strategy = _validate_and_fill_strategy(response_data, brief)

        logger.info(f"Generated brand strategy block for {brand_name}")
        return strategy

    except Exception as e:
        logger.error(f"Error generating brand strategy: {e}")
        return _generate_fallback_strategy(brief)


def _validate_and_fill_strategy(data: Dict[str, Any], brief: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate strategy data and fill in missing fields with fallbacks.

    Args:
        data: Raw LLM response (may be partial/invalid)
        brief: Original brief for fallback generation

    Returns:
        Complete strategy dict with all required fields
    """
    brand_name = brief.get("brand_name", "Your Brand")
    industry = brief.get("industry", "your industry")
    primary_customer = brief.get("primary_customer", "target customers")
    product_service = brief.get("product_service", "solutions")

    # Use Pydantic models to validate and fill defaults
    try:
        positioning = BrandPositioning(**(data.get("positioning", {})))
    except Exception:
        positioning = BrandPositioning(
            category=industry,
            target_audience=primary_customer,
            competitive_whitespace=f"Strategic advantage through {product_service}",
            benefit_statement="Measurable results and sustainable growth",
            reason_to_believe="Proven track record and industry expertise",
        )

    try:
        cultural_tension = CulturalTension(**(data.get("cultural_tension", {})))
    except Exception:
        cultural_tension = CulturalTension(
            tension_statement="Market demands efficiency without sacrificing quality",
            this_brand_believes=f"{brand_name} believes in strategic excellence and measurable impact",
            how_we_resolve_it="By combining expertise with systematic processes",
        )

    try:
        brand_archetype_data = data.get("brand_archetype", {})
        brand_archetype = BrandArchetype(**(brand_archetype_data))
    except Exception:
        brand_archetype = BrandArchetype(
            primary="Hero",
            secondary="Sage",
            description="The Hero archetype combined with Sage wisdom",
            on_brand_behaviours=[
                f"Taking bold action to solve {industry} challenges",
                f"Sharing expert insights with {primary_customer}",
                "Delivering measurable results consistently",
            ],
            off_brand_behaviours=[
                "Making promises without proof",
                "Using jargon instead of clarity",
                "Competing on price alone",
            ],
        )

    try:
        messaging_data = data.get("messaging_hierarchy", {})
        pillars_data = messaging_data.get("pillars", [])

        # Ensure we have at least 3 pillars
        if len(pillars_data) < 3:
            pillars_data = _generate_default_pillars(brief)

        pillars = [
            MessagingPillar(**p) if isinstance(p, dict) else p
            for p in pillars_data[:3]  # Take first 3
        ]

        messaging_hierarchy = MessagingHierarchy(
            brand_promise=messaging_data.get(
                "brand_promise",
                f"{brand_name} delivers measurable growth through strategic excellence.",
            ),
            pillars=pillars,
        )
    except Exception:
        pillars = _generate_default_pillars(brief)
        messaging_hierarchy = MessagingHierarchy(
            brand_promise=f"{brand_name} delivers measurable growth through strategic excellence.",
            pillars=pillars,
        )

    try:
        brand_story = BrandStory(**(data.get("brand_story", {})))
    except Exception:
        brand_story = BrandStory(
            hero=primary_customer,
            conflict=f"Struggling with fragmented {industry} strategies and inconsistent results",
            resolution=f"{brand_name} provides integrated strategy and expert execution",
            what_future_looks_like="Sustainable competitive advantage and measurable growth",
        )

    # Return as dict (not Pydantic object) for consistency
    return {
        "positioning": positioning.model_dump(),
        "cultural_tension": cultural_tension.model_dump(),
        "brand_archetype": brand_archetype.model_dump(),
        "messaging_hierarchy": messaging_hierarchy.model_dump(),
        "brand_story": brand_story.model_dump(),
    }


def _generate_default_pillars(brief: Dict[str, Any]) -> list:
    """Generate default messaging pillars from brief."""
    brand_name = brief.get("brand_name", "Your Brand")
    industry = brief.get("industry", "your industry")
    primary_customer = brief.get("primary_customer", "target customers")

    return [
        MessagingPillar(
            name="Strategic Expertise",
            description=f"{brand_name} combines deep {industry} knowledge with proven frameworks",
            rtbs=[
                f"15+ years of {industry} experience",
                f"Proven track record with {primary_customer}",
            ],
        ),
        MessagingPillar(
            name="Measurable Results",
            description="Every engagement includes transparent metrics and ROI tracking",
            rtbs=[
                "Average 3.2x ROI within 6 months",
                "Real-time performance dashboards",
            ],
        ),
        MessagingPillar(
            name="Long-Term Partnership",
            description=f"{brand_name} focuses on sustainable growth, not transactional projects",
            rtbs=[
                "Dedicated support and strategic advisory",
                "95% client retention rate",
            ],
        ),
    ]


def _generate_fallback_strategy(brief: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a safe fallback strategy when LLM fails.

    Args:
        brief: Original brief

    Returns:
        Complete fallback strategy dict
    """
    brand_name = brief.get("brand_name", "Your Brand")
    industry = brief.get("industry", "your industry")
    primary_customer = brief.get("primary_customer", "target customers")

    logger.info(f"Using fallback brand strategy for {brand_name}")

    return {
        "positioning": {
            "category": f"{industry} solutions provider",
            "target_audience": primary_customer,
            "competitive_whitespace": "Strategic partnership approach vs. transactional vendors",
            "benefit_statement": "Measurable growth through integrated strategy and expert execution",
            "reason_to_believe": f"{brand_name} combines proven frameworks with industry expertise",
        },
        "cultural_tension": {
            "tension_statement": "Customers demand both innovation and proven results",
            "this_brand_believes": f"{brand_name} believes in evidence-based strategy and sustainable growth",
            "how_we_resolve_it": "By combining best practices with customized approaches",
        },
        "brand_archetype": {
            "primary": "Hero",
            "secondary": "Sage",
            "description": "Strategic leaders who guide customers to competitive advantage through expertise and action",
            "on_brand_behaviours": [
                f"Taking bold action in {industry} markets",
                "Sharing transparent insights and metrics",
                "Delivering consistent measurable results",
            ],
            "off_brand_behaviours": [
                "Making unsubstantiated claims",
                "Avoiding accountability for results",
                "Using complexity to obscure lack of strategy",
            ],
        },
        "messaging_hierarchy": {
            "brand_promise": f"{brand_name} delivers sustainable competitive advantage through strategic excellence and measurable execution.",
            "pillars": [
                {
                    "name": "Strategic Partnership",
                    "description": f"{brand_name} acts as strategic advisor, not just service provider",
                    "rtbs": [
                        f"Dedicated account teams with {industry} expertise",
                        "Quarterly business reviews focused on growth",
                    ],
                },
                {
                    "name": "Measurable Impact",
                    "description": "Every decision backed by data and transparent reporting",
                    "rtbs": [
                        "Real-time performance dashboards",
                        "Average 3.2x ROI within 6 months",
                    ],
                },
                {
                    "name": "Sustainable Growth",
                    "description": "Focus on long-term competitive advantage, not short-term tactics",
                    "rtbs": [
                        "95% client retention rate",
                        "Clients typically increase investment year-over-year",
                    ],
                },
            ],
        },
        "brand_story": {
            "hero": primary_customer,
            "conflict": f"Operating in {industry} with fragmented tools, unclear strategy, and inconsistent results",
            "resolution": f"{brand_name} provides integrated strategy, proven frameworks, and expert execution",
            "what_future_looks_like": "Sustainable competitive advantage, market leadership position, predictable growth trajectory",
        },
    }


def strategy_dict_to_markdown(strategy: Dict[str, Any], brand_name: str = "Your Brand") -> str:
    """
    Convert brand strategy dict to well-formatted markdown.

    Args:
        strategy: Brand strategy dict with positioning, cultural_tension, etc.
        brand_name: Brand name for personalization

    Returns:
        Formatted markdown string
    """
    lines = [
        f"Strategic brand positioning defining how {brand_name} occupies distinct competitive space.\n",
    ]

    # Positioning Section
    pos = strategy.get("positioning", {})
    lines.append("## Positioning")
    lines.append(f"\n**Category**: {pos.get('category', 'Market category')}")
    lines.append(f"**Target Audience**: {pos.get('target_audience', 'Target customers')}")
    lines.append(
        f"**Competitive Whitespace**: {pos.get('competitive_whitespace', 'Unique position')}"
    )
    lines.append(f"**Core Benefit**: {pos.get('benefit_statement', 'Measurable growth')}")
    lines.append(f"**Reason to Believe**: {pos.get('reason_to_believe', 'Industry expertise')}\n")

    # Cultural Tension Section
    ct = strategy.get("cultural_tension", {})
    lines.append("## Cultural Tension")
    lines.append(f"\n**Tension Statement**: {ct.get('tension_statement', 'Market tension')}")
    lines.append(
        f"\n**What We Believe**: {ct.get('this_brand_believes', 'Brand belief statement')}"
    )
    lines.append(f"\n**How We Resolve It**: {ct.get('how_we_resolve_it', 'Resolution approach')}\n")

    # Brand Archetype Section
    ba = strategy.get("brand_archetype", {})
    lines.append("## Brand Archetype")
    lines.append(f"\n**Primary**: {ba.get('primary', 'Hero')}")
    lines.append(f"**Secondary**: {ba.get('secondary', 'Sage')}")
    lines.append(f"\n**Description**: {ba.get('description', 'Archetype description')}")

    on_brand = ba.get("on_brand_behaviours", [])
    if on_brand:
        lines.append("\n**On-Brand Behaviours**:")
        for behaviour in on_brand:
            lines.append(f"- {behaviour}")

    off_brand = ba.get("off_brand_behaviours", [])
    if off_brand:
        lines.append("\n**Off-Brand Behaviours to Avoid**:")
        for behaviour in off_brand:
            lines.append(f"- {behaviour}")
    lines.append("")

    # Messaging Hierarchy Section
    mh = strategy.get("messaging_hierarchy", {})
    lines.append("## Messaging Hierarchy")
    lines.append(f"\n**Brand Promise**: {mh.get('brand_promise', 'Core brand promise')}\n")
    lines.append("**Messaging Pillars**:")

    pillars = mh.get("pillars", [])
    for pillar in pillars:
        lines.append(
            f"\n- **{pillar.get('name', 'Pillar')}**: {pillar.get('description', 'Description')}"
        )
        rtbs = pillar.get("rtbs", [])
        if rtbs:
            for rtb in rtbs:
                lines.append(f"  - {rtb}")

    lines.append("")

    # Brand Story Section
    bs = strategy.get("brand_story", {})
    lines.append("## Brand Story")
    lines.append(f"\n**Hero**: {bs.get('hero', 'Protagonist')}")
    lines.append(f"\n**Conflict**: {bs.get('conflict', 'Obstacle faced')}")
    lines.append(f"\n**Resolution**: {bs.get('resolution', 'How we solve it')}")
    lines.append(f"\n**Future State**: {bs.get('what_future_looks_like', 'Transformed future')}")

    return "\n".join(lines)
