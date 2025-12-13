"""Production - DTOs."""
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
from aicmo.shared.ids import DraftId, StrategyId, AssetId

class ContentDraftDTO(BaseModel):
    draft_id: DraftId
    strategy_id: StrategyId
    content_type: str
    body: str
    metadata: Dict[str, Any] = {}
    created_at: datetime

class CreativeSpecDTO(BaseModel):
    format: str
    dimensions: str
    style_guide: Dict[str, Any] = {}

class AssetDTO(BaseModel):
    asset_id: AssetId
    asset_type: str
    url: str
    metadata: Dict[str, Any] = {}

class DraftBundleDTO(BaseModel):
    bundle_id: str
    draft_id: DraftId
    assets: List[AssetDTO]
    assembled_at: datetime

__all__ = ["ContentDraftDTO", "CreativeSpecDTO", "AssetDTO", "DraftBundleDTO"]
