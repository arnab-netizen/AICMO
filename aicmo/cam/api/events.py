"""
CAM (Client Acquisition) - Domain Events.

Events emitted by CAM for cross-module coordination.
"""

from datetime import datetime
from aicmo.shared.events import DomainEvent
from aicmo.shared.ids import LeadId, CampaignId, ClientId
from typing import Optional


class LeadIngested(DomainEvent):
    """Event: Raw lead ingested into CAM system."""
    
    lead_id: LeadId
    campaign_id: CampaignId
    source: str
    email: str


class LeadQualified(DomainEvent):
    """Event: Lead qualified with score/grade."""
    
    lead_id: LeadId
    grade: str
    score: float
    is_qualified: bool


class OutreachPlanned(DomainEvent):
    """Event: Outreach plan created for lead."""
    
    lead_id: LeadId
    channels: list[str]  # e.g., ["email", "linkedin"]
    message_count: int


class ClientSigned(DomainEvent):
    """
    Event: Lead converted to signed client.
    
    This is a critical event that triggers:
    - Onboarding workflow
    - Project setup
    - Billing initialization
    """
    
    client_id: ClientId
    original_lead_id: LeadId
    name: str
    email: str
    company: Optional[str] = None
    signed_at: datetime
    contract_value: Optional[float] = None


__all__ = [
    "LeadIngested",
    "LeadQualified",
    "OutreachPlanned",
    "ClientSigned",
]
