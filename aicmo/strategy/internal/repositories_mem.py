"""
Strategy module in-memory repository.

Provides same interface as DB repository but stores data in memory.
Simulates idempotency constraints for testing parity.

Idempotency Key: (brief_id, version)
- Simulates DB unique constraint behavior
- Duplicate (brief_id, version) raises ValueError (mimics IntegrityError)
"""

from typing import Dict, Optional
from aicmo.strategy.api.dtos import StrategyDocDTO
from aicmo.shared.ids import BriefId, StrategyId


class InMemoryStrategyRepo:
    """
    In-memory storage for strategies.
    
    Simulates DB behavior including idempotency constraints.
    """
    
    def __init__(self):
        self._strategies: Dict[StrategyId, StrategyDocDTO] = {}
        self._by_brief: Dict[BriefId, list[StrategyId]] = {}
        # Track (brief_id, version) combinations for idempotency
        self._brief_versions: Dict[tuple[BriefId, int], StrategyId] = {}
    
    def save(self, strategy: StrategyDocDTO) -> None:
        """
        Save strategy to memory.
        
        Idempotency: If (brief_id, version) already exists with different strategy_id,
        raises ValueError (simulates DB IntegrityError).
        If same strategy_id, updates in place (idempotent).
        """
        key = (strategy.brief_id, strategy.version)
        existing_id = self._brief_versions.get(key)
        
        if existing_id and existing_id != strategy.strategy_id:
            # Different strategy_id for same (brief_id, version) = constraint violation
            raise ValueError(
                f"Duplicate (brief_id, version): ({strategy.brief_id}, {strategy.version}) "
                f"already exists with strategy_id={existing_id}"
            )
        
        # Save strategy
        self._strategies[strategy.strategy_id] = strategy
        self._brief_versions[key] = strategy.strategy_id
        
        # Update brief index
        if strategy.brief_id not in self._by_brief:
            self._by_brief[strategy.brief_id] = []
        if strategy.strategy_id not in self._by_brief[strategy.brief_id]:
            self._by_brief[strategy.brief_id].append(strategy.strategy_id)
    
    def get(self, strategy_id: StrategyId) -> Optional[StrategyDocDTO]:
        """
        Retrieve strategy by ID.
        
        Read-only: Does NOT mutate any state.
        """
        return self._strategies.get(strategy_id)
    
    def list_by_brief(self, brief_id: BriefId) -> list[StrategyDocDTO]:
        """
        List all strategies for a brief, ordered by version.
        
        Read-only: Does NOT mutate any state.
        """
        strategy_ids = self._by_brief.get(brief_id, [])
        strategies = [self._strategies[sid] for sid in strategy_ids if sid in self._strategies]
        return sorted(strategies, key=lambda s: s.version)
