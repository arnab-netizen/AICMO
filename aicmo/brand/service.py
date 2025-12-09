"""
Brand Strategy Engine Service Layer.

Stage B: Functions for generating brand architecture, positioning, and narrative
from client intake data.
Stage K2: Enhanced with Kaizen-informed positioning decisions.
"""

from typing import Optional, List
import logging

from aicmo.brand.domain import (
    BrandCore,
    BrandPositioning,
    BrandArchitecture,
    BrandNarrative,
    BrandStrategy,
)
from aicmo.domain.intake import ClientIntake
from aicmo.learning.event_types import EventType
from aicmo.memory.engine import log_event
from aicmo.learning.domain import KaizenContext

logger = logging.getLogger(__name__)


def generate_brand_core(intake: ClientIntake, kaizen: Optional[KaizenContext] = None) -> BrandCore:
    """
    Generate brand core elements from client intake.
    
    Stage B: Creates purpose, vision, mission, values foundation.
    Stage K2: Considers successful positioning patterns from Kaizen.
    
    Args:
        intake: Client intake data
        kaizen: Optional Kaizen context with historical insights
        
    Returns:
        BrandCore with fundamental brand elements
        
    Note:
        Stage B implementation uses structured composition from intake.
        Future: Integrate with LLM for deeper brand philosophy generation.
    """
    logger.info(f"Generating brand core for {intake.brand_name}")
    
    # Stage B: Derive core from intake data
    # Future: LLM-powered brand philosophy generation
    
    purpose = _derive_purpose(intake)
    vision = _derive_vision(intake)
    mission = _derive_mission(intake)
    values = _derive_values(intake, kaizen)
    
    core = BrandCore(
        purpose=purpose,
        vision=vision,
        mission=mission,
        values=values,
        personality_traits=_derive_personality(intake, kaizen),
        voice_characteristics=_derive_voice(intake, kaizen)
    )
    
    # Validate brand core before returning (G1: contracts layer)
    from aicmo.core.contracts import validate_brand_core
    core = validate_brand_core(core)
    
    # Learning: Log brand core generation
    log_event(
        EventType.BRAND_CORE_GENERATED.value,
        project_id=intake.brand_name,
        details={
            "brand_name": intake.brand_name,
            "industry": intake.industry,
            "values_count": len(values),
            "kaizen_influenced": kaizen is not None
        },
        tags=["brand", "core", "foundation"]
    )
    
    return core


def generate_brand_positioning(intake: ClientIntake, kaizen: Optional[KaizenContext] = None) -> BrandPositioning:
    """
    Generate brand positioning framework.
    
    Stage B: Creates strategic positioning using classical framework.
    Stage K2: Applies successful positioning patterns from history.
    
    Args:
        intake: Client intake data
        kaizen: Optional Kaizen context with historical insights
        
    Returns:
        BrandPositioning with competitive positioning
    """
    logger.info(f"Generating brand positioning for {intake.brand_name}")
    
    # Stage K2: Check if Kaizen has successful positioning angles
    positioning_note = []
    if kaizen and kaizen.successful_positioning:
        logger.info(f"Kaizen: Applying {len(kaizen.successful_positioning)} proven positioning patterns")
        positioning_note = kaizen.successful_positioning[:2]
    
    # Stage B: Classical positioning framework
    audience = intake.target_audiences[0] if intake.target_audiences else "Business decision-makers"
    positioning = BrandPositioning(
        target_audience=audience,
        frame_of_reference=_derive_category(intake),
        point_of_difference=_derive_differentiation(intake, kaizen),
        reason_to_believe=_derive_rtb(intake),
        competitive_alternatives=_identify_alternatives(intake),
        key_benefits=_extract_benefits(intake, kaizen)
    )
    
    # Learning: Log positioning generation
    log_event(
        EventType.BRAND_POSITIONING_GENERATED.value,
        project_id=intake.brand_name,
        details={
            "brand_name": intake.brand_name,
            "industry": intake.industry,
            "frame_of_reference": positioning.frame_of_reference
        },
        tags=["brand", "positioning", "strategy"]
    )
    
    return positioning


def generate_brand_architecture(intake: ClientIntake) -> BrandArchitecture:
    """
    Generate brand architecture structure.
    
    Stage B: Creates brand hierarchy and strategic pillars.
    
    Args:
        intake: Client intake data
        
    Returns:
        BrandArchitecture with structure and pillars
    """
    logger.info(f"Generating brand architecture for {intake.brand_name}")
    
    # Stage B: Derive architecture from intake
    # Can integrate with existing strategy pillar generation
    pillars = _generate_strategic_pillars(intake)
    
    architecture = BrandArchitecture(
        project_id=intake.brand_name,
        core_brand_name=intake.brand_name,
        core_brand_description=f"{intake.brand_name} - {intake.industry} leader",
        sub_brands=[],  # Stage B: No sub-brands by default
        pillars=pillars,
        architecture_type="branded_house"  # Default for most clients
    )
    
    # Learning: Log architecture generation
    log_event(
        EventType.BRAND_ARCHITECTURE_GENERATED.value,
        project_id=intake.brand_name,
        details={
            "brand_name": intake.brand_name,
            "pillars_count": len(pillars),
            "architecture_type": architecture.architecture_type
        },
        tags=["brand", "architecture", "structure"]
    )
    
    return architecture


def generate_brand_narrative(
    architecture: BrandArchitecture,
    core: Optional[BrandCore] = None,
    positioning: Optional[BrandPositioning] = None
) -> BrandNarrative:
    """
    Generate brand narrative and storytelling framework.
    
    Stage B: Creates compelling brand story from architecture.
    
    Args:
        architecture: Brand architecture (required)
        core: Optional brand core elements
        positioning: Optional brand positioning
        
    Returns:
        BrandNarrative with story and messaging
    """
    logger.info(f"Generating brand narrative for {architecture.core_brand_name}")
    
    # Stage B: Compose narrative from architecture
    # Future: LLM-powered storytelling
    
    brand_story = _compose_brand_story(architecture, core, positioning)
    elevator_pitch = _create_elevator_pitch(architecture, positioning)
    key_messages = _derive_key_messages(architecture, core)
    
    narrative = BrandNarrative(
        project_id=architecture.project_id,
        brand_story=brand_story,
        tagline=_generate_tagline(architecture, positioning),
        elevator_pitch=elevator_pitch,
        rtbs=_extract_rtbs(core, positioning),
        key_messages=key_messages
    )
    
    # Learning: Log narrative generation
    log_event(
        EventType.BRAND_NARRATIVE_GENERATED.value,
        project_id=architecture.project_id or architecture.core_brand_name,
        details={
            "brand_name": architecture.core_brand_name,
            "story_length": len(brand_story),
            "key_messages_count": len(key_messages)
        },
        tags=["brand", "narrative", "storytelling"]
    )
    
    return narrative


def generate_complete_brand_strategy(intake: ClientIntake) -> BrandStrategy:
    """
    Generate complete brand strategy with all components.
    
    Stage B: One-stop function for full brand strategy development.
    
    Args:
        intake: Client intake data
        
    Returns:
        BrandStrategy with all components integrated
    """
    logger.info(f"Generating complete brand strategy for {intake.brand_name}")
    
    # Generate all components
    core = generate_brand_core(intake)
    positioning = generate_brand_positioning(intake)
    architecture = generate_brand_architecture(intake)
    narrative = generate_brand_narrative(architecture, core, positioning)
    
    # Compose complete strategy
    strategy = BrandStrategy(
        project_id=intake.brand_name,
        client_name=intake.brand_name,
        core=core,
        positioning=positioning,
        architecture=architecture,
        narrative=narrative,
        executive_summary=_create_executive_summary(intake, core, positioning),
        implementation_priorities=_identify_priorities(architecture, positioning),
        success_metrics=_define_success_metrics(intake)
    )
    
    return strategy


# ═══════════════════════════════════════════════════════════════════════
# Internal helper functions (Stage B: Rule-based implementations)
# Stage K2: Enhanced with Kaizen insights
# ═══════════════════════════════════════════════════════════════════════


def _derive_purpose(intake: ClientIntake) -> str:
    """Derive brand purpose from intake."""
    audience = intake.target_audiences[0] if intake.target_audiences else 'businesses'
    if intake.primary_goal:
        return f"To help {audience} {intake.primary_goal.lower()}"
    return f"To transform {intake.industry or 'the industry'} through innovation"


def _derive_vision(intake: ClientIntake) -> str:
    """Derive brand vision from intake."""
    return f"To be the leading {intake.industry or 'industry'} brand recognized for excellence and innovation"


def _derive_mission(intake: ClientIntake) -> str:
    """Derive brand mission from intake."""
    return f"Deliver exceptional {intake.industry or 'industry'} solutions that drive measurable results"


def _derive_values(intake: ClientIntake, kaizen: Optional[KaizenContext] = None) -> List[str]:
    """
    Derive brand values from intake.
    Stage K2: May adjust based on successful patterns.
    """
    base_values = ["Excellence", "Innovation", "Integrity", "Customer-First"]
    
    # Stage K2: If Kaizen shows data-driven approach wins, emphasize it
    if kaizen and "data-driven" in str(kaizen.successful_positioning).lower():
        base_values.insert(1, "Data-Driven")
    
    return base_values


def _derive_personality(intake: ClientIntake, kaizen: Optional[KaizenContext] = None) -> List[str]:
    """
    Derive brand personality traits.
    Stage K2: Favor tones that have historically performed well.
    """
    base_traits = ["Professional", "Innovative", "Trustworthy", "Bold"]
    
    # Stage K2: Apply effective tones from Kaizen
    if kaizen and kaizen.effective_tones:
        # Add successful tones while keeping base traits
        for tone in kaizen.effective_tones[:2]:
            if tone not in base_traits:
                base_traits.append(tone.capitalize())
    
    return base_traits


def _derive_voice(intake: ClientIntake, kaizen: Optional[KaizenContext] = None) -> List[str]:
    """
    Derive brand voice characteristics.
    Stage K2: Consider historical voice effectiveness.
    """
    return ["Clear", "Confident", "Authoritative", "Approachable"]


def _derive_category(intake: ClientIntake) -> str:
    """Derive competitive category."""
    return f"{intake.industry or 'Business'} solutions"


def _derive_differentiation(intake: ClientIntake, kaizen: Optional[KaizenContext] = None) -> str:
    """
    Derive point of difference.
    Stage K2: Emphasize successful differentiation patterns from history.
    """
    base_diff = f"AI-powered approach with proven results in {intake.industry or 'your industry'}"
    
    # Stage K2: If we have successful positioning patterns, mention them
    if kaizen and kaizen.successful_positioning:
        if "data-driven" in str(kaizen.successful_positioning).lower():
            base_diff = f"Data-driven, {base_diff.lower()}"
    
    return base_diff


def _derive_rtb(intake: ClientIntake) -> str:
    """Derive reason to believe."""
    return "Proven track record and data-driven methodology"


def _identify_alternatives(intake: ClientIntake) -> List[str]:
    """Identify competitive alternatives."""
    return ["Traditional agencies", "In-house teams", "Other platforms"]


def _extract_benefits(intake: ClientIntake, kaizen: Optional[KaizenContext] = None) -> List[str]:
    """
    Extract key benefits.
    Stage K2: Prioritize benefits that have historically resonated.
    """
    benefits = ["Faster results", "Lower cost", "Better quality"]
    
    # Stage K2: Add channel-specific benefits if Kaizen shows strong channels
    if kaizen and kaizen.best_channels:
        benefits.append(f"Proven success on {kaizen.best_channels[0]}")
    
    return benefits


def _generate_strategic_pillars(intake: ClientIntake) -> List[str]:
    """Generate strategic pillars."""
    # Stage B: Simple pillar generation
    # Future: Integrate with existing strategy.service pillar generation
    return [
        "Brand Awareness",
        "Customer Engagement",
        "Market Leadership"
    ]


def _compose_brand_story(
    architecture: BrandArchitecture,
    core: Optional[BrandCore],
    positioning: Optional[BrandPositioning]
) -> str:
    """Compose brand story from components."""
    story = f"{architecture.core_brand_name} exists to "
    
    if core:
        story += f"{core.purpose.lower()}. "
    
    story += f"We believe that {architecture.pillar_descriptions or 'excellence matters'}. "
    
    if positioning:
        story += f"For {positioning.target_audience}, we provide {positioning.point_of_difference}."
    
    return story


def _create_elevator_pitch(
    architecture: BrandArchitecture,
    positioning: Optional[BrandPositioning]
) -> str:
    """Create 30-second elevator pitch."""
    if positioning:
        return (
            f"{architecture.core_brand_name} is the {positioning.frame_of_reference} "
            f"that {positioning.point_of_difference}. We help {positioning.target_audience} "
            f"achieve their goals through proven strategies."
        )
    return f"{architecture.core_brand_name} delivers exceptional results."


def _derive_key_messages(architecture: BrandArchitecture, core: Optional[BrandCore]) -> List[str]:
    """Derive key brand messages."""
    messages = [
        f"{architecture.core_brand_name} delivers measurable results",
        "Proven methodology backed by data",
        "Expert team with deep industry knowledge"
    ]
    return messages


def _generate_tagline(
    architecture: BrandArchitecture,
    positioning: Optional[BrandPositioning]
) -> Optional[str]:
    """Generate brand tagline."""
    # Stage B: Simple tagline
    # Future: LLM-powered tagline generation
    return f"{architecture.core_brand_name}: Excellence in Action"


def _extract_rtbs(core: Optional[BrandCore], positioning: Optional[BrandPositioning]) -> List[str]:
    """Extract reasons to believe."""
    rtbs = []
    if positioning:
        rtbs.append(positioning.reason_to_believe)
    rtbs.extend(["Proven track record", "Industry expertise", "Data-driven results"])
    return rtbs


def _create_executive_summary(
    intake: ClientIntake,
    core: BrandCore,
    positioning: BrandPositioning
) -> str:
    """Create executive summary of strategy."""
    return (
        f"This brand strategy establishes {intake.brand_name} as a leader in {intake.industry}. "
        f"Our purpose is to {core.purpose}. We position ourselves as {positioning.point_of_difference} "
        f"for {positioning.target_audience}."
    )


def _identify_priorities(architecture: BrandArchitecture, positioning: BrandPositioning) -> List[str]:
    """Identify implementation priorities."""
    return [
        f"Establish {architecture.pillars[0]} foundation",
        "Build brand awareness in target market",
        "Execute initial campaigns"
    ]


def _define_success_metrics(intake: ClientIntake) -> List[str]:
    """Define success metrics."""
    return [
        "Brand awareness increase",
        "Customer engagement growth",
        "Market share gain"
    ]
