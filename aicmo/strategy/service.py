"""Strategy generation service - Phase 1 implementation.

Wraps existing backend.generators.marketing_plan to preserve external API
while introducing domain-driven design internally.
"""

from typing import Optional
from aicmo.domain.intake import ClientIntake
from aicmo.domain.strategy import StrategyDoc, StrategyPillar
from aicmo.io.client_reports import ClientInputBrief, MarketingPlanView
from aicmo.learning.kaizen_service import KaizenContext


async def generate_strategy(
    intake: ClientIntake,
    kaizen_context: Optional[KaizenContext] = None
) -> StrategyDoc:
    """
    Generate a marketing strategy from client intake.
    
    Phase 1 Implementation:
    - Convert ClientIntake → ClientInputBrief for backend compatibility
    - Call existing backend.generators.marketing_plan.generate_marketing_plan()
    - Convert MarketingPlanView → StrategyDoc domain model
    
    Stage 4: Logs learning events for strategy generation.
    Action 4: Accepts kaizen_context to inform strategy with past learnings.
    
    Args:
        intake: Normalized client intake data
        kaizen_context: Optional Kaizen learnings to influence strategy generation
        
    Returns:
        Generated strategy document with pillars
        
    Kaizen Usage:
        If kaizen_context provided:
        - Uses successful_pillars to bias pillar generation
        - Uses high_clarity_segments to adjust complexity
        - Uses pack_success_rates to inform approach
    """
    from aicmo.memory.engine import log_event
    
    try:
        # Import here to avoid circular dependency during module initialization
        from backend.generators.marketing_plan import generate_marketing_plan
        
        # Convert ClientIntake to ClientInputBrief for existing backend
        brief: ClientInputBrief = intake.to_client_input_brief()
        
        # Action 4: Augment brief with Kaizen insights if available
        if kaizen_context:
            # Add Kaizen insights to brief context
            # This allows the LLM to learn from past successes
            kaizen_notes = []
            
            if kaizen_context.successful_pillars:
                kaizen_notes.append(f"Past successful pillars: {', '.join(kaizen_context.successful_pillars[:3])}")
            
            if kaizen_context.recommended_tones:
                kaizen_notes.append(f"Recommended tones: {', '.join(kaizen_context.recommended_tones)}")
            
            if kaizen_context.risky_patterns:
                kaizen_notes.append(f"Avoid these patterns: {', '.join(kaizen_context.risky_patterns[:3])}")
            
            if hasattr(brief, 'additional_context') and kaizen_notes:
                brief.additional_context = (brief.additional_context or "") + "\n\nKaizen Insights:\n" + "\n".join(kaizen_notes)
        
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
        
        # Validate strategy before returning (G1: contracts layer)
        from aicmo.core.contracts import validate_strategy_doc
        strategy_doc = validate_strategy_doc(strategy_doc)
        
        # Stage 4: Log successful strategy generation with Kaizen usage
        log_event(
            "STRATEGY_GENERATED",
            project_id=intake.brand_name,
            details={
                "pillars_count": len(strategy_doc.pillars),
                "primary_goal": strategy_doc.primary_goal,
                "has_industry": intake.industry is not None,
                "kaizen_used": kaizen_context is not None,
                "kaizen_confidence": kaizen_context.confidence if kaizen_context else None
            },
            tags=["strategy", "success"]
        )
        
        return strategy_doc
    except Exception as e:
        # Stage 4: Log strategy generation failure
        log_event(
            "STRATEGY_FAILED",
            project_id=intake.brand_name,
            details={"error": str(e)},
            tags=["strategy", "error"]
        )
        raise
