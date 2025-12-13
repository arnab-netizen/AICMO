"""
CAM (Client Acquisition) - Port Interfaces.

Ports define the contract for CAM functionality without implementation details.
Split into Command ports (write) and Query ports (read-only).
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from aicmo.cam.api.dtos import (
    RawLeadDTO,
    LeadDTO,
    QualifiedLeadDTO,
    OutreachMessageDTO,
    OutreachPlanDTO,
    SignedClientDTO,
    LeadScoreDTO,
    LeadSummaryDTO,
    LeadStatusDTO,
)
from aicmo.shared.ids import LeadId, CampaignId, ClientId


# === Command Ports (Write Operations) ===

class LeadIngestPort(ABC):
    """Ingest raw leads from various sources."""
    
    @abstractmethod
    def ingest(self, raw_lead: RawLeadDTO, campaign_id: CampaignId) -> LeadId:
        """
        Ingest a raw lead into CAM system.
        
        Returns: Assigned LeadId
        """
        pass


class LeadQualifyPort(ABC):
    """Qualify and score leads."""
    
    @abstractmethod
    def qualify(self, lead_id: LeadId) -> QualifiedLeadDTO:
        """
        Qualify a lead (score, grade, routing).
        
        Returns: Qualified lead with score/grade
        """
        pass


class OutreachPlanPort(ABC):
    """Create outreach plans and messages."""
    
    @abstractmethod
    def create_plan(self, lead_id: LeadId) -> OutreachPlanDTO:
        """
        Generate personalized outreach plan for a lead.
        
        Returns: Multi-channel outreach plan
        """
        pass


class DealClosePort(ABC):
    """Mark deals as won/signed."""
    
    @abstractmethod
    def close_deal(self, lead_id: LeadId, signed_at: str) -> SignedClientDTO:
        """
        Mark lead as signed client.
        
        Returns: Signed client record with new ClientId
        Emits: ClientSigned event
        """
        pass


# === Query Ports (Read-Only Operations) ===

class CamQueryPort(ABC):
    """Read-only queries for CAM data."""
    
    @abstractmethod
    def get_lead(self, lead_id: LeadId) -> Optional[LeadDTO]:
        """Get lead by ID."""
        pass
    
    @abstractmethod
    def list_leads(
        self,
        campaign_id: Optional[CampaignId] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[LeadSummaryDTO]:
        """List leads with optional filters."""
        pass
    
    @abstractmethod
    def get_lead_score(self, lead_id: LeadId) -> Optional[LeadScoreDTO]:
        """Get lead score and reasons."""
        pass


__all__ = [
    # Command ports
    "LeadIngestPort",
    "LeadQualifyPort",
    "OutreachPlanPort",
    "DealClosePort",
    # Query ports
    "CamQueryPort",
]
