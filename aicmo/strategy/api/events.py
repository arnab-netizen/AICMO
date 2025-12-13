"""
Strategy - Domain Events.
"""

from aicmo.shared.events import DomainEvent
from aicmo.shared.ids import StrategyId, BriefId


class StrategyGenerated(DomainEvent):
    """Event: Strategy document generated."""
    
    strategy_id: StrategyId
    brief_id: BriefId
    version: int


class StrategyApproved(DomainEvent):
    """
    Event: Strategy approved by client/stakeholder.
    
    Triggers production phase.
    """
    
    strategy_id: StrategyId
    brief_id: BriefId
    approved_by: str


__all__ = ["StrategyGenerated", "StrategyApproved"]
