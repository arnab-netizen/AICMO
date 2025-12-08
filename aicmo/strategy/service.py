"""Strategy generation service - Phase 1 implementation.

Wraps existing backend.generators.marketing_plan to preserve external API
while introducing domain-driven design internally.
"""

from aicmo.domain.intake import ClientIntake
from aicmo.domain.strategy import StrategyDoc, StrategyPillar
from aicmo.io.client_reports import ClientInputBrief, MarketingPlanView


async def generate_strategy(intake: ClientIntake) -> StrategyDoc:
    """
    Generate a marketing strategy from client intake.
    
    Phase 1 Implementation:
    - Convert ClientIntake → ClientInputBrief for backend compatibility
    - Call existing backend.generators.marketing_plan.generate_marketing_plan()
    - Convert MarketingPlanView → StrategyDoc domain model
    
    Args:
        intake: Normalized client intake data
        
    Returns:
        Generated strategy document with pillars
    """
    # Import here to avoid circular dependency during module initialization
    from backend.generators.marketing_plan import generate_marketing_plan
    
    # Convert ClientIntake to ClientInputBrief for existing backend
    brief: ClientInputBrief = intake.to_client_input_brief()
    
    # Call existing strategy generation logic (LLM-powered)
    marketing_plan: MarketingPlanView = await generate_marketing_plan(brief)
    
    # Convert MarketingPlanView to StrategyDoc domain model
    strategy_doc = StrategyDoc(
        brand_name=intake.brand_name,
        industry=intake.industry,
        executive_summary=marketing_plan.executive_summary,
        situation_analysis=marketing_plan.situation_analysis,
        strategy_narrative=marketing_plan.strategy,
        pillars=[
            StrategyPillar(
                name=p.name,
                description=p.description or "",
                kpi_impact=p.kpi_impact or ""
            )
            for p in marketing_plan.pillars
        ],
        primary_goal=intake.primary_goal,
        timeline=intake.timeline
    )
    
    return strategy_doc
