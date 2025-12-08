"""Strategy document domain models."""

from typing import List, Optional
from enum import Enum

from .base import AicmoBaseModel


class StrategyStatus(str, Enum):
    """Strategy document approval status."""

    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class StrategyPillar(AicmoBaseModel):
    """Individual strategic pillar."""
    
    name: str
    description: str
    kpi_impact: str


class StrategyDoc(AicmoBaseModel):
    """
    Normalized strategy document.
    
    Contains the core strategic plan output from the strategy generation engine.
    """

    brand_name: str
    industry: Optional[str] = None
    
    executive_summary: str
    situation_analysis: str
    strategy_narrative: str
    
    pillars: List[StrategyPillar] = []
    
    primary_goal: Optional[str] = None
    timeline: Optional[str] = None
    
    status: StrategyStatus = StrategyStatus.DRAFT

    @classmethod
    def from_existing_response(cls, data) -> "StrategyDoc":
        """
        Adapter from existing strategy engine response.
        
        Args:
            data: Existing response object or dict
            
        Returns:
            Normalized StrategyDoc
        """
        if hasattr(data, "dict"):
            as_dict = data.dict()
        elif hasattr(data, "model_dump"):
            as_dict = data.model_dump()
        else:
            as_dict = dict(data)

        return cls(
            brand_name=as_dict.get("brand_name") or "Unknown",
            industry=as_dict.get("industry"),
            executive_summary=as_dict.get("executive_summary") or "",
            situation_analysis=as_dict.get("situation_analysis") or "",
            strategy_narrative=as_dict.get("strategy") or as_dict.get("strategy_narrative") or "",
            pillars=[
                StrategyPillar(
                    name=p.get("name", ""),
                    description=p.get("description", ""),
                    kpi_impact=p.get("kpi_impact", "")
                )
                for p in as_dict.get("pillars", [])
            ],
            primary_goal=as_dict.get("primary_goal"),
            timeline=as_dict.get("timeline"),
        )
