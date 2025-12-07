"""
Pydantic models for Brand Strategy Block structure.

Defines structured representations of brand positioning, cultural tension,
brand archetypes, messaging hierarchy, and brand story.
"""

from typing import List
from pydantic import BaseModel, Field


class BrandPositioning(BaseModel):
    """Brand positioning with core market position details."""

    category: str = Field(default="", description="The category {brand} operates in")
    target_audience: str = Field(default="", description="Primary audience for the brand")
    competitive_whitespace: str = Field(
        default="", description="The unique competitive space the brand occupies"
    )
    benefit_statement: str = Field(default="", description="Core benefit delivered to customers")
    reason_to_believe: str = Field(
        default="", description="Why customers should believe this brand"
    )


class CulturalTension(BaseModel):
    """Cultural tension framework for brand relevance."""

    tension_statement: str = Field(
        default="", description="The cultural tension the brand addresses"
    )
    this_brand_believes: str = Field(
        default="", description="What this brand believes about the tension"
    )
    how_we_resolve_it: str = Field(default="", description="How the brand resolves the tension")


class BrandArchetype(BaseModel):
    """Brand archetype framework defining brand personality."""

    primary: str = Field(default="", description="Primary archetype (e.g., Hero, Sage, Creator)")
    secondary: str = Field(default="", description="Secondary archetype for depth")
    description: str = Field(default="", description="Description of the archetype combination")
    on_brand_behaviours: List[str] = Field(
        default_factory=list, description="Examples of on-brand behaviors"
    )
    off_brand_behaviours: List[str] = Field(
        default_factory=list, description="Examples of off-brand behaviors to avoid"
    )


class MessagingPillar(BaseModel):
    """Single messaging pillar with supporting reasons to believe."""

    name: str = Field(default="", description="Pillar name/title")
    description: str = Field(default="", description="Pillar description")
    rtbs: List[str] = Field(
        default_factory=list, description="Reasons to believe supporting this pillar"
    )


class MessagingHierarchy(BaseModel):
    """Messaging hierarchy with brand promise and pillars."""

    brand_promise: str = Field(default="", description="The core promise the brand makes")
    pillars: List[MessagingPillar] = Field(default_factory=list, description="List of 3 pillars")


class BrandStory(BaseModel):
    """Brand story components using hero-conflict-resolution."""

    hero: str = Field(default="", description="The protagonist (customer persona)")
    conflict: str = Field(default="", description="The obstacle or tension")
    resolution: str = Field(default="", description="How the brand resolves the conflict")
    what_future_looks_like: str = Field(default="", description="Future state after success")


class BrandStrategyBlock(BaseModel):
    """Complete brand strategy block."""

    positioning: BrandPositioning = Field(default_factory=BrandPositioning)
    cultural_tension: CulturalTension = Field(default_factory=CulturalTension)
    brand_archetype: BrandArchetype = Field(default_factory=BrandArchetype)
    messaging_hierarchy: MessagingHierarchy = Field(default_factory=MessagingHierarchy)
    brand_story: BrandStory = Field(default_factory=BrandStory)
