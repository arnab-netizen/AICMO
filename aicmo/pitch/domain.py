"""
Pitch & Proposal Engine Domain Models.

Stage P: Business development AI for prospect qualification, pitch deck generation,
and proposal creation.
"""

from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class Prospect(BaseModel):
    """
    Prospect information for pitch/proposal generation.
    
    Represents a potential client in the sales pipeline.
    """
    
    id: Optional[int] = None
    name: str = Field(..., description="Contact name")
    company: str = Field(..., description="Company name")
    industry: str = Field(..., description="Industry/vertical")
    company_size: Optional[str] = Field(None, description="e.g., '50-200 employees', 'Enterprise'")
    region: Optional[str] = Field(None, description="Geographic region")
    
    # Pain points & needs
    pain_points: List[str] = Field(default_factory=list, description="Key challenges they face")
    goals: List[str] = Field(default_factory=list, description="What they want to achieve")
    
    # Budget & timeline
    budget_range: Optional[str] = Field(None, description="e.g., '$50k-$100k', 'TBD'")
    timeline: Optional[str] = Field(None, description="e.g., 'Q1 2026', 'Urgent'")
    
    # Context
    discovery_notes: Optional[str] = Field(None, description="Notes from discovery call")
    source: Optional[str] = Field(None, description="How we found them: 'inbound', 'referral', 'outbound'")
    
    # Status
    stage: str = Field(default="prospect", description="Sales stage: prospect, qualified, pitched, negotiation")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PitchSection(BaseModel):
    """
    One section of a pitch deck.
    """
    
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content/talking points")
    slide_type: str = Field(default="content", description="text, image, chart, etc.")
    order: int = Field(..., description="Position in deck")


class PitchDeck(BaseModel):
    """
    Generated pitch deck for a prospect.
    
    Structured presentation to win business.
    """
    
    id: Optional[int] = None
    prospect_id: Optional[int] = Field(None, description="Associated prospect")
    
    # Core content
    title: str = Field(..., description="Deck title")
    subtitle: Optional[str] = Field(None, description="Deck subtitle")
    sections: List[PitchSection] = Field(default_factory=list, description="Deck sections/slides")
    
    # Summary
    executive_summary: Optional[str] = Field(None, description="One-paragraph overview")
    key_benefits: List[str] = Field(default_factory=list, description="Top 3-5 benefits")
    
    # Meta
    target_duration_minutes: int = Field(default=30, description="Expected presentation length")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1, description="Deck version number")


class ProposalScope(BaseModel):
    """
    Scope of work for a proposal.
    """
    
    deliverable: str = Field(..., description="What will be delivered")
    description: str = Field(..., description="Details of deliverable")
    timeline: Optional[str] = Field(None, description="When it will be delivered")


class ProposalPricing(BaseModel):
    """
    Pricing structure for a proposal.
    """
    
    item: str = Field(..., description="Line item name")
    description: Optional[str] = Field(None, description="Pricing details")
    amount: float = Field(..., description="Price in USD")
    unit: Optional[str] = Field(None, description="e.g., 'per month', 'one-time'")


class Proposal(BaseModel):
    """
    Formal proposal document for a prospect.
    
    Detailed scope, pricing, timeline, and terms.
    """
    
    id: Optional[int] = None
    prospect_id: Optional[int] = Field(None, description="Associated prospect")
    
    # Overview
    title: str = Field(..., description="Proposal title")
    executive_summary: str = Field(..., description="High-level overview")
    
    # Scope
    scope: List[ProposalScope] = Field(default_factory=list, description="What we'll deliver")
    
    # Pricing
    pricing: List[ProposalPricing] = Field(default_factory=list, description="Pricing breakdown")
    total_amount: Optional[float] = Field(None, description="Total proposal value")
    
    # Timeline
    project_duration: Optional[str] = Field(None, description="e.g., '3 months', '12 weeks'")
    start_date: Optional[str] = Field(None, description="Expected start date")
    
    # Terms
    payment_terms: Optional[str] = Field(None, description="e.g., '50% upfront, 50% on delivery'")
    terms_and_conditions: Optional[str] = Field(None, description="Legal terms")
    
    # Meta
    valid_until: Optional[datetime] = Field(None, description="Proposal expiration")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1, description="Proposal version")
    status: str = Field(default="draft", description="draft, sent, accepted, rejected")


class PitchOutcome(BaseModel):
    """
    Result of a pitch/proposal.
    
    Used for learning and tracking win/loss patterns.
    """
    
    prospect_id: int
    pitch_deck_id: Optional[int] = None
    proposal_id: Optional[int] = None
    
    outcome: str = Field(..., description="won, lost, pending")
    deal_value: Optional[float] = Field(None, description="If won, deal size in USD")
    
    # Learning data
    win_factors: List[str] = Field(default_factory=list, description="What helped us win")
    loss_reasons: List[str] = Field(default_factory=list, description="Why we lost")
    
    feedback: Optional[str] = Field(None, description="Prospect feedback")
    competitor: Optional[str] = Field(None, description="Who they chose instead (if lost)")
    
    decided_at: datetime = Field(default_factory=datetime.utcnow)
