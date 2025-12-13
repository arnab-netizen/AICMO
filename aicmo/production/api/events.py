"""Production - Events."""
from aicmo.shared.events import DomainEvent
from aicmo.shared.ids import DraftId, AssetId

class DraftReady(DomainEvent):
    draft_id: DraftId
    content_type: str

class AssetGenerated(DomainEvent):
    asset_id: AssetId
    asset_type: str

__all__ = ["DraftReady", "AssetGenerated"]
