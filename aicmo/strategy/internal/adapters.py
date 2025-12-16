"""Strategy module - Internal adapters (MVP + DB persistence)."""
from datetime import datetime, timezone
from typing import Optional, Protocol
from aicmo.strategy.api.ports import StrategyGeneratePort, StrategyApprovePort, StrategyQueryPort
from aicmo.strategy.api.dtos import (
    StrategyInputDTO,
    StrategyDocDTO,
    StrategyVersionDTO,
    KpiDTO,
    ChannelPlanDTO,
    TimelineDTO,
)
from aicmo.shared.ids import BriefId, StrategyId


# ============================================================================
# Repository Protocol (allows both inmemory and DB implementations)
# ============================================================================

class StrategyRepository(Protocol):
    """Repository interface for strategy persistence."""
    
    def save(self, strategy: StrategyDocDTO) -> None:
        """Save a strategy document."""
        ...
    
    def get(self, strategy_id: StrategyId) -> Optional[StrategyDocDTO]:
        """Retrieve a strategy by ID."""
        ...
    
    def list_by_brief(self, brief_id: BriefId) -> list[StrategyDocDTO]:
        """List all strategies for a brief."""
        ...


# ============================================================================
# Port Adapters (use repository via dependency injection)
# ============================================================================

class StrategyGenerateAdapter(StrategyGeneratePort):
    """Minimal strategy generation adapter."""
    
    def __init__(self, repo: StrategyRepository):
        self._repo = repo
    
    def generate(self, brief_id: BriefId, input_data: StrategyInputDTO) -> StrategyDocDTO:
        """
        Generate strategy from brief.
        
        MVP: Returns deterministic template strategy.
        """
        strategy_id = StrategyId(f"strat_{brief_id}_{int(datetime.now(timezone.utc).timestamp())}")
        
        strategy = StrategyDocDTO(
            strategy_id=strategy_id,
            brief_id=brief_id,
            version=1,
            kpis=[
                KpiDTO(name="Lead Generation", target_value=500, unit="leads", timeframe_days=90),
                KpiDTO(name="Engagement Rate", target_value=5.5, unit="percent", timeframe_days=90),
            ],
            channels=[
                ChannelPlanDTO(
                    channel="linkedin",
                    budget_allocation_pct=40.0,
                    tactics=["Thought leadership posts", "Sponsored content"],
                ),
                ChannelPlanDTO(
                    channel="email",
                    budget_allocation_pct=30.0,
                    tactics=["Nurture campaigns", "Newsletter"],
                ),
            ],
            timeline=TimelineDTO(
                milestones=[
                    {"name": "Strategy Approval", "week": "1"},
                    {"name": "Content Creation", "week": "2-4"},
                    {"name": "Campaign Launch", "week": "5"},
                ],
                duration_weeks=8,
            ),
            executive_summary="Multi-channel B2B marketing strategy focused on thought leadership and lead generation.",
            is_approved=False,
            created_at=datetime.now(timezone.utc),
        )
        
        self._repo.save(strategy)
        return strategy


class StrategyApproveAdapter(StrategyApprovePort):
    """Minimal strategy approval adapter."""
    
    def __init__(self, repo: StrategyRepository):
        self._repo = repo
    
    def approve(self, strategy_id: StrategyId, approved_by: str) -> StrategyDocDTO:
        """Mark strategy as approved."""
        strategy = self._repo.get(strategy_id)
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        # Update approval status (creates new DTO, preserves immutability)
        updated_strategy = StrategyDocDTO(
            strategy_id=strategy.strategy_id,
            brief_id=strategy.brief_id,
            version=strategy.version,
            kpis=strategy.kpis,
            channels=strategy.channels,
            timeline=strategy.timeline,
            executive_summary=strategy.executive_summary,
            is_approved=True,
            created_at=strategy.created_at,
            approved_at=datetime.now(timezone.utc),
        )
        
        self._repo.save(updated_strategy)
        return updated_strategy


class StrategyQueryAdapter(StrategyQueryPort):
    """Minimal query adapter."""
    
    def __init__(self, repo: StrategyRepository):
        self._repo = repo
    
    def get_strategy(self, strategy_id: StrategyId) -> Optional[StrategyDocDTO]:
        return self._repo.get(strategy_id)
    
    def list_versions(self, brief_id: BriefId) -> list[StrategyVersionDTO]:
        strategies = self._repo.list_by_brief(brief_id)
        return [
            StrategyVersionDTO(
                strategy_id=s.strategy_id,
                version=s.version,
                is_approved=s.is_approved,
                created_at=s.created_at,
            )
            for s in strategies
        ]
