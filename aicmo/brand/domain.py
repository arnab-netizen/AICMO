"""
Brand Strategy Engine Domain Models.

Stage B: Brand architecture, positioning, narrative generation for comprehensive
brand strategy development.
"""

from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class BrandCore(BaseModel):
    """
    Core brand foundation elements.
    
    The fundamental beliefs and aspirations that define the brand.
    """
    
    purpose: str = Field(..., description="Why the brand exists beyond making money")
    vision: str = Field(..., description="Long-term aspiration for the brand")
    mission: str = Field(..., description="What the brand does to fulfill its purpose")
    values: List[str] = Field(..., description="Core values that guide behavior")
    
    personality_traits: Optional[List[str]] = Field(None, description="Brand personality attributes")
    voice_characteristics: Optional[List[str]] = Field(None, description="How the brand communicates")


class BrandPositioning(BaseModel):
    """
    Strategic brand positioning framework.
    
    Defines how the brand competes and differentiates in the market.
    """
    
    target_audience: str = Field(..., description="Primary audience description")
    frame_of_reference: str = Field(..., description="Competitive category/context")
    point_of_difference: str = Field(..., description="Unique differentiator")
    reason_to_believe: str = Field(..., description="Why the POD is credible")
    
    # Optional extended positioning
    audience_segments: Optional[List[str]] = Field(None, description="Detailed audience segments")
    competitive_alternatives: Optional[List[str]] = Field(None, description="What customers would use instead")
    key_benefits: Optional[List[str]] = Field(None, description="Primary benefits delivered")


class BrandArchitecture(BaseModel):
    """
    Brand architecture structure.
    
    Defines the relationship between master brand, sub-brands, and pillars.
    """
    
    id: Optional[int] = None
    project_id: Optional[str] = None
    
    # Core brand
    core_brand_name: str = Field(..., description="Master brand name")
    core_brand_description: str = Field(..., description="What the core brand represents")
    
    # Sub-brands
    sub_brands: List[str] = Field(default_factory=list, description="Product/service sub-brands")
    
    # Strategic pillars
    pillars: List[str] = Field(..., description="Key strategic pillars (3-5 recommended)")
    pillar_descriptions: Optional[dict] = Field(None, description="Details for each pillar")
    
    # Architecture type
    architecture_type: str = Field(
        default="branded_house",
        description="branded_house, house_of_brands, hybrid, endorsed"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BrandNarrative(BaseModel):
    """
    Brand narrative and storytelling framework.
    
    The compelling story that brings the brand to life.
    """
    
    id: Optional[int] = None
    project_id: Optional[str] = None
    
    # Core narrative
    brand_story: str = Field(..., description="Long-form brand story")
    tagline: Optional[str] = Field(None, description="Brand tagline/slogan")
    elevator_pitch: str = Field(..., description="30-second brand description")
    
    # Supporting elements
    origin_story: Optional[str] = Field(None, description="How the brand came to be")
    customer_story: Optional[str] = Field(None, description="Typical customer journey")
    
    # Reasons to believe
    rtbs: List[str] = Field(default_factory=list, description="Reasons to believe in the brand")
    proof_points: List[str] = Field(default_factory=list, description="Evidence/credentials")
    
    # Messaging
    key_messages: List[str] = Field(default_factory=list, description="Core messages (3-5)")
    message_pillars: Optional[dict] = Field(None, description="Message framework by pillar")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BrandStrategy(BaseModel):
    """
    Complete brand strategy combining all elements.
    
    Comprehensive brand strategy document.
    """
    
    id: Optional[int] = None
    project_id: Optional[str] = None
    client_name: str
    
    # Core components
    core: BrandCore
    positioning: BrandPositioning
    architecture: BrandArchitecture
    narrative: BrandNarrative
    
    # Executive summary
    executive_summary: Optional[str] = Field(None, description="Strategy overview")
    
    # Implementation notes
    implementation_priorities: Optional[List[str]] = Field(None, description="What to do first")
    success_metrics: Optional[List[str]] = Field(None, description="How to measure success")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1)
