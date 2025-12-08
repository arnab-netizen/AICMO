"""Strategy document domain models."""

from typing import Any, Dict, Optional
from enum import Enum

from .base import AicmoBaseModel


class StrategyStatus(str, Enum):
    """Strategy document approval status."""

    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class StrategyDoc(AicmoBaseModel):
    """
    Normalized strategy document.
    
    Wraps the output from strategy generation with metadata
    for tracking and approval workflows.
    """

    project_id: Optional[int] = None
    title: str
    summary: str
    raw_payload: Dict[str, Any]
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
            title=as_dict.get("title")
            or as_dict.get("plan_title")
            or "Strategy",
            summary=as_dict.get("summary")
            or as_dict.get("overview")
            or "",
            raw_payload=as_dict,
        )
