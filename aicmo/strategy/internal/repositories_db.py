"""
Strategy module database repository.

Implements strategy persistence using SQLAlchemy ORM.
Follows same session lifecycle pattern as onboarding module.

Idempotency Key: (brief_id, version)
- Enforced by unique constraint at DB level
- Duplicate (brief_id, version) will raise IntegrityError
"""

from datetime import datetime, timezone
from typing import Optional, Protocol
from sqlalchemy.exc import IntegrityError

from aicmo.strategy.api.dtos import (
    StrategyDocDTO,
    StrategyVersionDTO,
    KpiDTO,
    ChannelPlanDTO,
    TimelineDTO,
)
from aicmo.shared.ids import BriefId, StrategyId


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


class DatabaseStrategyRepo:
    """
    Database storage for strategies using SQLAlchemy.
    
    Session Lifecycle: Uses same pattern as onboarding (aicmo.core.db.get_session)
    Idempotency: (brief_id, version) uniqueness enforced by DB constraint
    """
    
    def __init__(self):
        # Import DB models and session here to avoid circular imports
        from aicmo.strategy.internal.models import StrategyDocumentDB
        from aicmo.core.db import get_session
        
        self._StrategyDocumentDB = StrategyDocumentDB
        self._get_session = get_session
    
    def save(self, strategy: StrategyDocDTO) -> None:
        """
        Save strategy to database.
        
        Idempotency: If (brief_id, version) already exists, raises IntegrityError.
        Caller should handle this as idempotent success (same input = same state).
        
        Commit boundary: Explicit commit after successful insert/update.
        Rollback: Automatic on exception via context manager.
        """
        with self._get_session() as session:
            strategy_db = self._StrategyDocumentDB(
                id=strategy.strategy_id,
                brief_id=strategy.brief_id,
                version=strategy.version,
                kpis=self._serialize_kpis(strategy.kpis),
                channels=self._serialize_channels(strategy.channels),
                timeline=self._serialize_timeline(strategy.timeline),
                executive_summary=strategy.executive_summary,
                is_approved=strategy.is_approved,
                approved_at=strategy.approved_at,
                created_at=strategy.created_at,
                updated_at=datetime.now(timezone.utc),
            )
            
            try:
                session.merge(strategy_db)  # Use merge to handle updates
                session.commit()
            except IntegrityError as e:
                # (brief_id, version) uniqueness violation = idempotency key collision
                # This is expected behavior for idempotent operations
                session.rollback()
                raise e
    
    def get(self, strategy_id: StrategyId) -> Optional[StrategyDocDTO]:
        """
        Retrieve strategy from database.
        
        Read-only: Does NOT mutate updated_at or any other field.
        """
        with self._get_session() as session:
            strategy_db = session.query(self._StrategyDocumentDB).filter_by(id=strategy_id).first()
            if not strategy_db:
                return None
            
            return self._to_dto(strategy_db)
    
    def list_by_brief(self, brief_id: BriefId) -> list[StrategyDocDTO]:
        """
        List all strategies for a brief.
        
        Read-only: Does NOT mutate any database state.
        """
        with self._get_session() as session:
            strategies_db = (
                session.query(self._StrategyDocumentDB)
                .filter_by(brief_id=brief_id)
                .order_by(self._StrategyDocumentDB.version.asc())
                .all()
            )
            return [self._to_dto(s) for s in strategies_db]
    
    def _serialize_kpis(self, kpis: list[KpiDTO]) -> list[dict]:
        """Convert KPI DTOs to JSON-serializable dicts."""
        return [kpi.model_dump() for kpi in kpis]
    
    def _serialize_channels(self, channels: list[ChannelPlanDTO]) -> list[dict]:
        """Convert Channel DTOs to JSON-serializable dicts."""
        return [channel.model_dump() for channel in channels]
    
    def _serialize_timeline(self, timeline: TimelineDTO) -> dict:
        """Convert Timeline DTO to JSON-serializable dict."""
        return timeline.model_dump()
    
    def _to_dto(self, strategy_db) -> StrategyDocDTO:
        """
        Convert DB model to DTO.
        
        Maps ORM model fields to DTO, deserializing JSON fields back to DTOs.
        """
        return StrategyDocDTO(
            strategy_id=strategy_db.id,
            brief_id=strategy_db.brief_id,
            version=strategy_db.version,
            kpis=[KpiDTO(**kpi) for kpi in (strategy_db.kpis or [])],
            channels=[ChannelPlanDTO(**ch) for ch in (strategy_db.channels or [])],
            timeline=TimelineDTO(**(strategy_db.timeline or {})),
            executive_summary=strategy_db.executive_summary,
            is_approved=strategy_db.is_approved,
            approved_at=strategy_db.approved_at,
            created_at=strategy_db.created_at,
        )
