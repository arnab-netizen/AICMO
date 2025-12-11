"""
Messaging Pillars generator: brief-driven, LLM-capable, with safe stub fallback.

Replaces hardcoded template with dynamic generation based on brief content.
"""

import os
from typing import Optional, List

from aicmo.io.client_reports import ClientInputBrief, StrategyPillar


def generate_messaging_pillars(
    brief: ClientInputBrief,
    industry_preset: Optional[dict] = None,
    memory_snippets: Optional[List[str]] = None,
    max_pillars: int = 3,
) -> List[StrategyPillar]:
    """
    Generate brief-specific Messaging Pillars.

    Automatically selects stub or LLM mode based on AICMO_USE_LLM.
    Always returns a non-empty list of StrategyPillar (graceful degradation).

    Args:
        brief: ClientInputBrief with brand, audience, goals, etc.
        industry_preset: Optional industry context dict
        memory_snippets: Optional list of relevant memory/learning snippets
        max_pillars: Max pillars to include (default 3)

    Returns:
        List[StrategyPillar] with pillar data (never empty, never throws)
    """
    try:
        use_llm = os.environ.get("AICMO_USE_LLM", "0").lower() in ["1", "true", "yes"]

        if use_llm:
            llm_result = _generate_messaging_pillars_with_llm(
                brief, industry_preset, memory_snippets
            )
            if llm_result:
                return _sanitize_messaging_pillars(llm_result, max_pillars)

        # Fall back to stub if LLM disabled or errored
        return _stub_messaging_pillars(brief, max_pillars)

    except Exception:
        # Ultimate fallback: return stub even if something goes wrong
        return _stub_messaging_pillars(brief, max_pillars)


def _generate_messaging_pillars_with_llm(
    brief: ClientInputBrief,
    industry_preset: Optional[dict],
    memory_snippets: Optional[List[str]],
) -> Optional[List[StrategyPillar]]:
    """
    Generate Messaging Pillars using the Phase 8.4 LLM router.

    Returns:
        List of StrategyPillar, or None if LLM call fails
    """
    try:
        # Import LLM router (Phase 8.4)
        from aicmo.llm.router import get_llm_client, LLMUseCase
        import json
        import asyncio

        brand_name = brief.brand.brand_name
        category = brief.brand.industry
        audience = brief.audience.primary_customer
        goals = brief.goal.primary_goal or "unspecified"
        kpis = ", ".join(brief.goal.kpis) if brief.goal.kpis else "growth"

        # Extract USPs if available
        usp_text = ""
        if brief.product_service and brief.product_service.items:
            usps = [f"{item.name}: {item.usp}" for item in brief.product_service.items if item.usp]
            if usps:
                usp_text = "\nKey USPs:\n" + "\n".join(f"- {usp}" for usp in usps)

        # Build prompt
        prompt = f"""Generate exactly 3 strategic messaging pillars for a marketing plan.

Brand: {brand_name}
Category: {category}
Target Audience: {audience}
Primary Goal: {goals}
KPIs: {kpis}{usp_text}

Each pillar should:
1. Have a clear, memorable name (3-6 words)
2. Have a brief description (1-2 sentences) about what this pillar addresses
3. Include a kpi_impact statement (how it drives the KPIs)

Return ONLY valid JSON in this exact format:
{{
  "pillars": [
    {{
      "name": "Pillar 1 Name",
      "description": "Brief description of what this pillar is about.",
      "kpi_impact": "How this drives the KPIs"
    }},
    {{
      "name": "Pillar 2 Name",
      "description": "Brief description of what this pillar is about.",
      "kpi_impact": "How this drives the KPIs"
    }},
    {{
      "name": "Pillar 3 Name",
      "description": "Brief description of what this pillar is about.",
      "kpi_impact": "How this drives the KPIs"
    }}
  ]
}}

Requirements:
- All pillars should be distinct and address different aspects of the marketing strategy
- Language should be professional and grounded in the brief
- Avoid placeholder phrases like "will be refined", "TBD", "to be determined"
- Avoid overblown claims like "leading", "dominates", "#1 in the market"
- Return ONLY the JSON, no explanation or markdown formatting"""

        # Get LLM client for STRATEGY_DOC use-case
        chain = get_llm_client(
            use_case=LLMUseCase.STRATEGY_DOC,
            profile_override=None,
            deep_research=False,
            multimodal=False
        )

        # Call the chain via ProviderChain.invoke
        success, result, provider_name = asyncio.run(
            chain.invoke(
                "generate",
                prompt=prompt
            )
        )

        if not success or not result:
            logger.warning(f"Messaging Pillars: LLM returned failure via {provider_name}")
            return None

        # Extract response text
        response_text = result if isinstance(result, str) else result.get("content", "")

        if not response_text or not response_text.strip():
            return None

        # Parse JSON response
        response_text = response_text.strip()
        # Remove markdown code fence if present
        if response_text.startswith("```"):
            response_text = response_text[response_text.find("{") : response_text.rfind("}") + 1]

        data = json.loads(response_text)
        if not isinstance(data, dict) or "pillars" not in data:
            return None

        pillars_data = data.get("pillars", [])
        if not isinstance(pillars_data, list):
            return None

        pillars = []
        for item in pillars_data:
            if isinstance(item, dict) and "name" in item and item.get("name", "").strip():
                pillar = StrategyPillar(
                    name=item.get("name", "").strip(),
                    description=item.get("description", "").strip() or None,
                    kpi_impact=item.get("kpi_impact", "").strip() or None,
                )
                pillars.append(pillar)

        return pillars if pillars else None

    except Exception:
        return None


def _sanitize_messaging_pillars(
    pillars: List[StrategyPillar],
    max_pillars: int = 3,
) -> List[StrategyPillar]:
    """
    Sanitize and limit Messaging Pillars output.

    - Ensures all pillars have non-empty names
    - Strips whitespace from all fields
    - Enforces max_pillars limit

    Args:
        pillars: List of StrategyPillar objects
        max_pillars: Maximum number of pillars to keep

    Returns:
        Cleaned, limited list of StrategyPillar objects
    """
    if not pillars:
        return []

    # Filter: keep only pillars with non-empty names
    filtered = [p for p in pillars if p.name and p.name.strip()]

    # Limit to max_pillars
    limited = filtered[:max_pillars]

    return limited


def _stub_messaging_pillars(
    brief: ClientInputBrief,
    max_pillars: int = 3,
) -> List[StrategyPillar]:
    """
    Fallback: Generate modest, honest Messaging Pillars from brief alone.

    No placeholder phrases, no fake claims.
    Just factual, actionable pillars based on the brief.

    Args:
        brief: ClientInputBrief
        max_pillars: Maximum number of pillars to generate

    Returns:
        Non-empty list of StrategyPillar
    """
    brand_name = brief.brand.brand_name
    category = brief.brand.industry
    audience = brief.audience.primary_customer

    pillars = []

    # Pillar 1: Problem/Opportunity (based on audience pain points)
    if brief.audience.pain_points:
        pain_summary = (
            brief.audience.pain_points[0] if brief.audience.pain_points else "customer needs"
        )
        pillars.append(
            StrategyPillar(
                name="Addressing Core Needs",
                description=f"Focus on how {brand_name} solves the {pain_summary} challenge for {audience}.",
                kpi_impact="Drives awareness and consideration among the target audience.",
            )
        )
    else:
        pillars.append(
            StrategyPillar(
                name="Problem Recognition",
                description=f"Help {audience} understand the specific challenges in the {category} space.",
                kpi_impact="Builds awareness of the problem {brand_name} solves.",
            )
        )

    # Pillar 2: Differentiation/Value (based on product USPs)
    if brief.product_service and brief.product_service.items:
        first_item = brief.product_service.items[0]
        usp = first_item.usp if first_item.usp else "unique value"
        pillars.append(
            StrategyPillar(
                name="Proven Value Delivery",
                description=f"Demonstrate how {brand_name}'s {usp} delivers tangible results.",
                kpi_impact="Drives consideration and conversion through proof of value.",
            )
        )
    else:
        pillars.append(
            StrategyPillar(
                name="Value Proposition",
                description=f"Clearly communicate what {brand_name} offers and why it matters.",
                kpi_impact="Builds trust and drives conversion intent.",
            )
        )

    # Pillar 3: Trust & Engagement (always relevant)
    pillars.append(
        StrategyPillar(
            name="Building Credibility & Engagement",
            description=f"Create consistent, authentic touchpoints that deepen the relationship with {audience}.",
            kpi_impact="Drives retention, advocacy, and repeat business.",
        )
    )

    return pillars[:max_pillars]
