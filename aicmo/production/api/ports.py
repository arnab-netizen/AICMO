"""Production - Port Interfaces."""
from abc import ABC, abstractmethod
from aicmo.production.api.dtos import ContentDraftDTO, AssetDTO, DraftBundleDTO
from aicmo.shared.ids import StrategyId, DraftId

class DraftGeneratePort(ABC):
    @abstractmethod
    def generate_draft(self, strategy_id: StrategyId) -> ContentDraftDTO:
        pass

class AssetAssemblePort(ABC):
    @abstractmethod
    def assemble_bundle(self, draft_id: DraftId) -> DraftBundleDTO:
        pass

class ProductionQueryPort(ABC):
    @abstractmethod
    def get_draft(self, draft_id: DraftId) -> ContentDraftDTO:
        pass

__all__ = ["DraftGeneratePort", "AssetAssemblePort", "ProductionQueryPort"]
