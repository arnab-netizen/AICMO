"""Delivery - DTOs."""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from aicmo.shared.ids import DraftId, DeliveryPackageId

class DeliveryArtifactDTO(BaseModel):
    name: str
    url: str
    format: str

class DeliveryPackageDTO(BaseModel):
    package_id: DeliveryPackageId
    draft_id: DraftId
    artifacts: List[DeliveryArtifactDTO]
    created_at: datetime

class PublishJobDTO(BaseModel):
    job_id: str
    package_id: DeliveryPackageId
    destination: str
    config: Dict[str, Any] = {}

class PublishResultDTO(BaseModel):
    job_id: str
    success: bool
    published_urls: List[str] = []
    error_message: Optional[str] = None
    published_at: Optional[datetime] = None

__all__ = ["DeliveryArtifactDTO", "DeliveryPackageDTO", "PublishJobDTO", "PublishResultDTO"]
