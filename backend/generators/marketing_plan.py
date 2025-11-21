"""LLM-powered marketing plan generator for AICMO."""

from typing import Optional

from aicmo.io.client_reports import (
    ClientInputBrief,
    MarketingPlanView,
    StrategyPillar,
)
from backend.dependencies import get_llm


async def generate_marketing_plan(brief: ClientInputBrief) -> MarketingPlanView:
    """
    Generate a highly structured marketing plan using LLM.

    Based strictly on the client brief, generates:
    - Executive summary
    - Situation analysis
    - Strategy narrative
    - 3 strategic pillars with KPI impact

    Args:
        brief: Structured client input brief

    Returns:
        MarketingPlan: Fully populated marketing plan
    """
    llm = get_llm()

    # Build industry context if available
    industry_context = ""
    if brief.brand.industry:
        industry_context = f"\nIndustry: {brief.brand.industry}"
    if brief.brand.business_type:
        industry_context += f"\nBusiness Type: {brief.brand.business_type}"

    prompt = f"""You are AICMO, a senior marketing strategist from Ogilvy.

Generate a highly structured, specific marketing plan based strictly on this client brief:

CLIENT BRIEF:
{brief.model_dump_json(indent=2)}
{industry_context}

GENERATE THESE SECTIONS (use ### headers):

### Executive Summary
3–5 paragraphs covering:
- Current situation
- Opportunity
- Strategic direction

### Situation Analysis
Market dynamics, audience insights, competitive landscape, and category tensions.
Be specific - reference the client's business type, industry, geography, and scale.

### Strategy
Core narrative and funnel structure for growth.
Should directly address the primary goal.

### Strategy Pillars
List exactly 3 pillars. Format each as:
- Pillar Name: [1-2 sentence description]
  KPI Impact: [How this drives the primary goal]

IMPORTANT:
- Do NOT use placeholders like "Not specified" or generic statements
- Fill missing data using logical inference from the industry and business type
- Make recommendations specific to the scale, budget, and constraints
- Be authoritative and client-ready
- All text should feel senior-level strategic

Return well-formatted markdown sections."""

    text = await llm.generate(prompt, temperature=0.75, max_tokens=3000)

    # Extract sections from LLM response
    summary = _extract_section(text, "Executive Summary")
    situation = _extract_section(text, "Situation Analysis")
    strategy = _extract_section(text, "Strategy")
    pillars = _extract_pillars(text)

    return MarketingPlanView(
        executive_summary=summary or "Strategic marketing plan generated.",
        situation_analysis=situation or "Market analysis indicates strong opportunity.",
        strategy=strategy or "Growth through strategic positioning and execution.",
        pillars=pillars,
    )


def _extract_section(text: str, section_name: str) -> Optional[str]:
    """Extract a section from LLM response by header name."""
    lines = text.split("\n")
    in_section = False
    section_content = []

    for line in lines:
        if f"### {section_name}" in line or f"## {section_name}" in line:
            in_section = True
            continue

        if in_section:
            # Stop at next header
            if line.startswith("###") or line.startswith("##"):
                break
            section_content.append(line)

    content = "\n".join(section_content).strip()
    return content if content else None


def _extract_pillars(text: str) -> list[StrategyPillar]:
    """Extract strategy pillars from LLM response."""
    pillars = []
    lines = text.split("\n")
    in_pillars = False

    current_pillar = None
    current_desc = []

    for line in lines:
        if "### Strategy Pillars" in line or "## Strategy Pillars" in line:
            in_pillars = True
            continue

        if in_pillars:
            if line.startswith("###") or line.startswith("##"):
                # Save previous pillar
                if current_pillar:
                    desc = " ".join(current_desc).strip()
                    pillars.append(
                        StrategyPillar(
                            name=current_pillar,
                            description=desc,
                            kpi_impact="Aligns growth objectives with KPIs",
                        )
                    )
                break

            if line.strip().startswith("- "):
                # New pillar
                if current_pillar:
                    desc = " ".join(current_desc).strip()
                    pillars.append(
                        StrategyPillar(
                            name=current_pillar,
                            description=desc,
                            kpi_impact="Aligns growth objectives with KPIs",
                        )
                    )

                # Parse pillar name and description
                rest = line.strip()[2:].strip()  # Remove "- "
                if ":" in rest:
                    name_part, desc_part = rest.split(":", 1)
                    current_pillar = name_part.strip()
                    current_desc = [desc_part.strip()]
                else:
                    current_pillar = rest
                    current_desc = []

            elif line.strip().startswith("KPI Impact:"):
                # Extract KPI impact
                if current_pillar:
                    kpi_text = line.split("KPI Impact:", 1)[1].strip()
                    desc = " ".join(current_desc).strip()
                    pillars.append(
                        StrategyPillar(
                            name=current_pillar,
                            description=desc,
                            kpi_impact=kpi_text,
                        )
                    )
                    current_pillar = None
                    current_desc = []

            elif current_pillar and line.strip():
                current_desc.append(line.strip())

    # Save last pillar
    if current_pillar:
        desc = " ".join(current_desc).strip()
        pillars.append(
            StrategyPillar(
                name=current_pillar,
                description=desc,
                kpi_impact="Aligns growth objectives with KPIs",
            )
        )

    # Ensure we have exactly 3 pillars
    while len(pillars) < 3:
        pillars.append(
            StrategyPillar(
                name=f"Growth Pillar {len(pillars) + 1}",
                description="Strategic growth initiative",
                kpi_impact="Drives primary business objective",
            )
        )

    return pillars[:3]
