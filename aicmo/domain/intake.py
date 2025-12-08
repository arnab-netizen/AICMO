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
    product_service: Optional[str] = None

    offers: List[str] = []
    target_audiences: List[str] = []
    primary_customer: Optional[str] = None

    primary_goal: Optional[str] = None
    primary_goal_description: Optional[str] = None
    timeline: Optional[str] = None

    kpi_notes: Optional[str] = None
    constraints: Optional[str] = None
    must_include: Optional[str] = None
    do_not_do: Optional[str] = None

    def to_client_input_brief(self):
        """
        Convert ClientIntake to backend's ClientInputBrief format.
        
        This adapter allows the new domain model to work with
        existing backend generators without breaking changes.
        
        Returns:
            ClientInputBrief compatible with existing backend code
        """
        from aicmo.io.client_reports import (
            ClientInputBrief,
            BrandBrief,
            AudienceBrief,
            GoalBrief,
            VoiceBrief,
            ProductServiceBrief,
            AssetsConstraintsBrief,
            OperationsBrief,
            StrategyExtrasBrief,
        )
        
        return ClientInputBrief(
            brand=BrandBrief(
                brand_name=self.brand_name,
                industry=self.industry or "General",
                product_service=self.product_service or "Products and services",
                primary_goal=self.primary_goal or self.primary_goal_description or "Growth",
                primary_customer=self.primary_customer or (self.target_audiences[0] if self.target_audiences else "Target customers"),
                timeline=self.timeline or "90 days",
                location=self.geography,
            ),
            audience=AudienceBrief(
                primary_customer=self.primary_customer or (self.target_audiences[0] if self.target_audiences else "Target customers"),
            ),
            goal=GoalBrief(
                primary_goal=self.primary_goal or self.primary_goal_description or "Growth",
                timeline=self.timeline or "90 days",
            ),
            voice=VoiceBrief(),
            product_service=ProductServiceBrief(),
            assets_constraints=AssetsConstraintsBrief(
                constraints=[self.constraints] if self.constraints else [],
            ),
            operations=OperationsBrief(),
            strategy_extras=StrategyExtrasBrief(
                must_include_messages=self.must_include,
                must_avoid_messages=self.do_not_do,
            ),
        )

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
            product_service=as_dict.get("product_service"),
            offers=as_dict.get("offers") or [],
            target_audiences=as_dict.get("target_audiences") or [],
            primary_customer=as_dict.get("primary_customer"),
            primary_goal=as_dict.get("primary_goal") or as_dict.get("goal"),
            primary_goal_description=as_dict.get("primary_goal_description"),
            timeline=as_dict.get("timeline"),
            kpi_notes=as_dict.get("kpis") or as_dict.get("kpi_notes"),
            constraints=as_dict.get("constraints"),
            must_include=as_dict.get("must_include"),
            do_not_do=as_dict.get("do_not_do"),
        )
