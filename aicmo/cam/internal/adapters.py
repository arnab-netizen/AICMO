"""
CAM Module - Internal Adapters (Minimal MVP for Phase 3).

Phase 3 Note:
This adapter provides a minimal ACL (Anti-Corruption Layer) over existing
CAM database access. Full CAM refactoring is deferred to Phase 4.

The adapter wraps existing CAM logic to prevent direct db_models imports
from outside modules.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from aicmo.cam.api.ports import CampaignCommandPort, CampaignQueryPort
from aicmo.cam.api.dtos import (
    CampaignCreateDTO,
    CampaignDTO,
    CampaignStatusDTO,
    LeadDTO,
)
from aicmo.shared.ids import CampaignId, LeadId, ClientId


class InMemoryCampaignRepo:
    """
    In-memory storage for campaigns (Phase 3 - no new DB writes).
    
    Note: Existing CAM tables remain. This repo is for NEW workflows
    that don't yet write to DB.
    """
    
    def __init__(self):
        self._campaigns: Dict[CampaignId, CampaignDTO] = {}
        self._leads: Dict[LeadId, LeadDTO] = {}
    
    def save_campaign(self, campaign: CampaignDTO) -> None:
        self._campaigns[campaign.campaign_id] = campaign
    
    def get_campaign(self, campaign_id: CampaignId) -> Optional[CampaignDTO]:
        return self._campaigns.get(campaign_id)
    
    def save_lead(self, lead: LeadDTO) -> None:
        self._leads[lead.lead_id] = lead


class CampaignCommandAdapter(CampaignCommandPort):
    """Minimal campaign command adapter (ACL over existing CAM)."""
    
    def __init__(self, repo: InMemoryCampaignRepo):
        self._repo = repo
    
    def create_campaign(self, create_dto: CampaignCreateDTO) -> CampaignDTO:
        """Create new campaign (in-memory for Phase 3)."""
        campaign_id = CampaignId(f"cam_{create_dto.client_id}_{int(datetime.utcnow().timestamp())}")
        
        campaign = CampaignDTO(
            campaign_id=campaign_id,
            client_id=create_dto.client_id,
            name=create_dto.name,
            status="ACTIVE",
            created_at=datetime.utcnow(),
            config={},
        )
        
        self._repo.save_campaign(campaign)
        return campaign


class CampaignQueryAdapter(CampaignQueryPort):
    """Minimal campaign query adapter."""
    
    def __init__(self, repo: InMemoryCampaignRepo):
        self._repo = repo
    
    def get_campaign(self, campaign_id: CampaignId) -> Optional[CampaignDTO]:
        return self._repo.get_campaign(campaign_id)
    
    def get_status(self, campaign_id: CampaignId) -> CampaignStatusDTO:
        campaign = self._repo.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        return CampaignStatusDTO(
            campaign_id=campaign_id,
            status=campaign.status,
            total_leads=0,
            active_leads=0,
            last_updated=campaign.created_at,
        )
