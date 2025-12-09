"""
Pitch & Proposal Engine Service Layer.

Stage P: Functions for generating pitch decks and proposals from prospect data.
Stage K2: Enhanced with Kaizen-informed decisions.
"""

from typing import Optional
import logging

from aicmo.pitch.domain import (
    Prospect, 
    PitchDeck, 
    PitchSection,
    Proposal,
    ProposalScope,
    ProposalPricing,
    PitchOutcome
)
from aicmo.learning.event_types import EventType
from aicmo.memory.engine import log_event
from aicmo.learning.domain import KaizenContext

logger = logging.getLogger(__name__)


def generate_pitch_deck(prospect: Prospect, kaizen: Optional[KaizenContext] = None) -> PitchDeck:
    """
    Generate a pitch deck for a prospect.
    
    Stage P: Creates structured pitch presentation based on prospect profile.
    Stage K2: Uses Kaizen insights to tailor pitch based on historical wins.
    
    Args:
        prospect: Prospect information
        kaizen: Optional Kaizen context with historical insights
        
    Returns:
        PitchDeck with sections tailored to prospect
        
    Raises:
        NotImplementedError: Full LLM-based generation not yet implemented
        
    Future:
        - Integrate with strategy/pack engines for content
        - Use Kaizen to learn from past pitch outcomes
        - Generate slides/visuals with templates
    """
    logger.info(f"Generating pitch deck for prospect: {prospect.company}")
    
    # Stage K2: Check if Kaizen has insights for this industry
    kaizen_note = ""
    if kaizen and kaizen.pitch_win_patterns:
        for pattern in kaizen.pitch_win_patterns:
            if "successful_industries" in pattern:
                if prospect.industry in pattern["successful_industries"]:
                    win_rate = pattern.get("win_rate", 0)
                    kaizen_note = f"\n\n[Kaizen Insight: We have a {win_rate*100:.0f}% win rate in {prospect.industry}. Emphasizing proven success.]"
                    logger.info(f"Kaizen: Found win pattern for {prospect.industry} industry")
    
    # Stage P: Basic structured pitch deck
    # Future: Integrate with LLM and existing strategy engines
    
    sections = [
        PitchSection(
            title="Problem Statement",
            content=_generate_problem_section(prospect, kaizen),
            slide_type="text",
            order=1
        ),
        PitchSection(
            title="Our Solution",
            content=_generate_solution_section(prospect, kaizen),
            slide_type="text",
            order=2
        ),
        PitchSection(
            title="Why Us",
            content=_generate_why_us_section(prospect, kaizen) + kaizen_note,
            slide_type="text",
            order=3
        ),
        PitchSection(
            title="Case Studies",
            content=_generate_case_studies_section(prospect, kaizen),
            slide_type="text",
            order=4
        ),
        PitchSection(
            title="Investment & Timeline",
            content=_generate_investment_section(prospect, kaizen),
            slide_type="text",
            order=5
        ),
    ]
    
    pitch_deck = PitchDeck(
        prospect_id=prospect.id,
        title=f"Marketing Strategy for {prospect.company}",
        subtitle=f"Tailored approach for {prospect.industry}",
        sections=sections,
        executive_summary=f"Comprehensive marketing strategy to help {prospect.company} achieve their goals.",
        key_benefits=[
            "Data-driven strategy aligned with your goals",
            "Proven frameworks from similar industries",
            "Rapid deployment with measurable results"
        ],
        target_duration_minutes=30
    )
    
    # Validate pitch deck before returning (G1: contracts layer)
    from aicmo.core.contracts import validate_pitch_deck
    pitch_deck = validate_pitch_deck(pitch_deck)
    
    # Learning: Log pitch deck generation
    log_event(
        EventType.PITCH_DECK_GENERATED.value,
        project_id=f"prospect_{prospect.id}" if prospect.id else prospect.company,
        details={
            "prospect_company": prospect.company,
            "prospect_industry": prospect.industry,
            "sections_count": len(sections),
            "budget_range": prospect.budget_range
        },
        tags=["pitch", "bizdev", "deck_generation"]
    )
    
    # Also log general pitch created event
    log_event(
        EventType.PITCH_CREATED.value,
        project_id=f"prospect_{prospect.id}" if prospect.id else prospect.company,
        details={
            "prospect_company": prospect.company,
            "stage": prospect.stage
        },
        tags=["pitch", "bizdev"]
    )
    
    return pitch_deck


def generate_proposal(prospect: Prospect, pitch_deck: Optional[PitchDeck] = None) -> Proposal:
    """
    Generate a formal proposal for a prospect.
    
    Stage P: Creates detailed proposal with scope, pricing, timeline.
    
    Args:
        prospect: Prospect information
        pitch_deck: Optional associated pitch deck
        
    Returns:
        Proposal document
        
    Raises:
        NotImplementedError: Full pricing/scope generation not yet implemented
        
    Future:
        - Integrate with pack pricing models
        - Use historical win rates to optimize pricing
        - Generate legal terms from templates
    """
    logger.info(f"Generating proposal for prospect: {prospect.company}")
    
    # Stage P: Basic structured proposal
    # Future: Integrate with pricing engine and legal templates
    
    scope_items = _generate_scope_items(prospect)
    pricing_items = _generate_pricing_items(prospect, scope_items)
    
    total = sum(item.amount for item in pricing_items)
    
    proposal = Proposal(
        prospect_id=prospect.id,
        title=f"Marketing Strategy Proposal for {prospect.company}",
        executive_summary=_generate_proposal_summary(prospect),
        scope=scope_items,
        pricing=pricing_items,
        total_amount=total,
        project_duration=prospect.timeline or "3 months",
        payment_terms="50% upfront, 25% at midpoint, 25% on delivery",
        terms_and_conditions="Standard AICMO terms apply. See attached.",
        status="draft"
    )
    
    # Learning: Log proposal generation
    log_event(
        EventType.PROPOSAL_GENERATED.value,
        project_id=f"prospect_{prospect.id}" if prospect.id else prospect.company,
        details={
            "prospect_company": prospect.company,
            "prospect_industry": prospect.industry,
            "total_amount": total,
            "scope_items_count": len(scope_items),
            "has_pitch_deck": pitch_deck is not None
        },
        tags=["pitch", "bizdev", "proposal"]
    )
    
    return proposal


def record_pitch_outcome(outcome: PitchOutcome) -> None:
    """
    Record the outcome of a pitch/proposal for learning.
    
    Stage P: Logs win/loss for Kaizen to learn from.
    
    Args:
        outcome: Pitch outcome details
        
    Future:
        - Feed into Kaizen for win/loss pattern analysis
        - Update pricing models based on win rates
        - Identify successful pitch structures
    """
    logger.info(f"Recording pitch outcome: {outcome.outcome} for prospect {outcome.prospect_id}")
    
    if outcome.outcome == "won":
        log_event(
            EventType.PITCH_WON.value,
            project_id=f"prospect_{outcome.prospect_id}",
            details={
                "deal_value": outcome.deal_value,
                "win_factors": outcome.win_factors,
                "feedback": outcome.feedback
            },
            tags=["pitch", "bizdev", "won", "success"]
        )
    elif outcome.outcome == "lost":
        log_event(
            EventType.PITCH_LOST.value,
            project_id=f"prospect_{outcome.prospect_id}",
            details={
                "loss_reasons": outcome.loss_reasons,
                "competitor": outcome.competitor,
                "feedback": outcome.feedback
            },
            tags=["pitch", "bizdev", "lost", "learning"]
        )


# ═══════════════════════════════════════════════════════════════════════
# Internal helper functions (Stage P: Simple implementations)
# Stage K2: Enhanced with Kaizen insights
# ═══════════════════════════════════════════════════════════════════════


def _generate_problem_section(prospect: Prospect, kaizen: Optional[KaizenContext] = None) -> str:
    """Generate problem statement section content."""
    if prospect.pain_points:
        problems = "\n".join(f"• {pain}" for pain in prospect.pain_points[:3])
        return f"Key challenges facing {prospect.company}:\n\n{problems}"
    else:
        return f"Common challenges in the {prospect.industry} industry that we help solve."


def _generate_solution_section(prospect: Prospect, kaizen: Optional[KaizenContext] = None) -> str:
    """Generate solution section content."""
    if prospect.goals:
        goals = "\n".join(f"• {goal}" for goal in prospect.goals[:3])
        return f"Our approach to achieving your goals:\n\n{goals}"
    else:
        return "Data-driven marketing strategy with proven frameworks."


def _generate_why_us_section(prospect: Prospect, kaizen: Optional[KaizenContext] = None) -> str:
    """
    Generate 'why choose us' section content.
    Stage K2: Enhanced with historical success data from Kaizen.
    """
    base = (
        f"AICMO brings:\n"
        f"• Deep expertise in {prospect.industry}\n"
        f"• Rapid deployment (weeks, not months)\n"
        f"• Measurable results with clear KPIs\n"
        f"• Continuous optimization through AI"
    )
    
    # Stage K2: Add proven track record if Kaizen has data
    if kaizen and kaizen.pitch_win_patterns:
        for pattern in kaizen.pitch_win_patterns:
            if pattern.get("total_wins", 0) > 0:
                base += f"\n• {pattern['total_wins']} successful campaigns with proven results"
                break
    
    return base


def _generate_case_studies_section(prospect: Prospect, kaizen: Optional[KaizenContext] = None) -> str:
    """
    Generate case studies section content.
    Stage K2: Reference successful industries from Kaizen.
    """
    # Stage P: Placeholder
    # Future: Pull real case studies from similar industries
    
    base = f"Case studies from similar companies in {prospect.industry}"
    
    # Stage K2: Mention industries where we've won
    if kaizen and kaizen.pitch_win_patterns:
        for pattern in kaizen.pitch_win_patterns:
            industries = pattern.get("successful_industries", [])
            if industries and prospect.industry in industries:
                base += f" and proven success across {', '.join(industries[:2])}"
                break
    
    return base + " (details available on request)."


def _generate_investment_section(prospect: Prospect, kaizen: Optional[KaizenContext] = None) -> str:
    """Generate investment/timeline section content."""
    budget = prospect.budget_range or "Custom pricing based on scope"
    timeline = prospect.timeline or "Flexible timeline"
    return f"Investment: {budget}\nTimeline: {timeline}"


def _generate_scope_items(prospect: Prospect) -> list[ProposalScope]:
    """Generate scope of work items."""
    # Stage P: Basic scope based on prospect needs
    # Future: Integrate with pack definitions
    
    items = [
        ProposalScope(
            deliverable="Marketing Strategy & Plan",
            description="Comprehensive strategy document with pillars, tactics, and KPIs",
            timeline="Week 1-2"
        ),
        ProposalScope(
            deliverable="Creative Assets",
            description="Platform-specific creative content (social, ads, etc.)",
            timeline="Week 2-4"
        ),
        ProposalScope(
            deliverable="Campaign Execution",
            description="Launch and initial optimization across channels",
            timeline="Week 4-8"
        ),
    ]
    
    return items


def _generate_pricing_items(prospect: Prospect, scope: list[ProposalScope]) -> list[ProposalPricing]:
    """Generate pricing items."""
    # Stage P: Simplified pricing
    # Future: Pull from actual pack pricing, apply win-rate optimized discounts
    
    items = [
        ProposalPricing(
            item="Strategy Development",
            description="Full marketing strategy and plan",
            amount=15000.0,
            unit="one-time"
        ),
        ProposalPricing(
            item="Creative Production",
            description="Creative assets for campaigns",
            amount=10000.0,
            unit="one-time"
        ),
        ProposalPricing(
            item="Campaign Management",
            description="3 months of campaign execution",
            amount=25000.0,
            unit="total"
        ),
    ]
    
    return items


def _generate_proposal_summary(prospect: Prospect) -> str:
    """Generate proposal executive summary."""
    return (
        f"This proposal outlines a comprehensive marketing strategy for {prospect.company} "
        f"to address key challenges in {prospect.industry} and achieve measurable growth. "
        f"Our approach combines data-driven strategy, rapid creative production, and "
        f"continuous optimization to deliver results."
    )
