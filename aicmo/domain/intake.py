"""Client intake domain models."""

from typing import Optional, List
from enum import Enum

from .base import AicmoBaseModel


class GoalMetric(str, Enum):
    """Primary marketing goal types."""

    AWARENESS = "awareness"
    LEADS = "leads"
    SALES = "sales"
    ENGAGEMENT = "engagement"
    OTHER = "other"


class ClientIntake(AicmoBaseModel):
    """
    Normalized client intake model.
    
    This represents the essential information needed to generate
    a marketing strategy, regardless of the source format.
    """

    brand_name: str
    industry: Optional[str] = None
    geography: Optional[str] = None

    offers: List[str] = []
    target_audiences: List[str] = []

    primary_goal: Optional[GoalMetric] = None
    primary_goal_description: Optional[str] = None

    kpi_notes: Optional[str] = None
    constraints: Optional[str] = None
    must_include: Optional[str] = None
    do_not_do: Optional[str] = None

    @classmethod
    def from_existing_request(cls, data) -> "ClientIntake":
        """
        Adapter from existing workflow request model or dict.
        Keep mapping defensive and non-breaking.
        
        Args:
            data: Existing request object or dict
            
        Returns:
            Normalized ClientIntake
        """
        if hasattr(data, "dict"):
            as_dict = data.dict()
        elif hasattr(data, "model_dump"):
            as_dict = data.model_dump()
        else:
            as_dict = dict(data)

        return cls(
            brand_name=as_dict.get("brand_name")
            or as_dict.get("client_name")
            or "Unknown",
            industry=as_dict.get("industry"),
            geography=as_dict.get("geo") or as_dict.get("geography"),
            offers=as_dict.get("offers") or [],
            target_audiences=as_dict.get("target_audiences") or [],
            primary_goal_description=as_dict.get("primary_goal")
            or as_dict.get("goal"),
            kpi_notes=as_dict.get("kpis") or as_dict.get("kpi_notes"),
            constraints=as_dict.get("constraints"),
            must_include=as_dict.get("must_include"),
            do_not_do=as_dict.get("do_not_do"),
        )
