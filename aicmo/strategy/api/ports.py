"""
Strategy - Port Interfaces.

Handles strategy generation and approval.
"""

from abc import ABC, abstractmethod
from typing import Optional
from aicmo.strategy.api.dtos import StrategyInputDTO, StrategyDocDTO, StrategyVersionDTO
from aicmo.shared.ids import BriefId, StrategyId, ClientId


class StrategyGeneratePort(ABC):
    """Generate strategy documents."""
    
    @abstractmethod
    def generate(self, brief_id: BriefId, input_data: StrategyInputDTO) -> StrategyDocDTO:
        """Generate strategy doc from brief."""
        pass


class StrategyApprovePort(ABC):
    """Approve strategy explicitly."""
    
    @abstractmethod
    def approve(self, strategy_id: StrategyId, approved_by: str) -> StrategyDocDTO:
        """Mark strategy as approved."""
        pass


class StrategyQueryPort(ABC):
    """Read strategy versions."""
    
    @abstractmethod
    def get_strategy(self, strategy_id: StrategyId) -> Optional[StrategyDocDTO]:
        """Get strategy by ID."""
        pass
    
    @abstractmethod
    def list_versions(self, brief_id: BriefId) -> list[StrategyVersionDTO]:
        """List all strategy versions for a brief."""
        pass


__all__ = ["StrategyGeneratePort", "StrategyApprovePort", "StrategyQueryPort"]
