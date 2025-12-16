"""
QC module database repository.

Implements QC result persistence using SQLAlchemy ORM.
Follows same session lifecycle pattern as Strategy/Production modules.

Idempotency Key: draft_id (unique constraint)
- One QC result per draft at a time
- Re-evaluation replaces existing result
"""

from datetime import datetime, timezone
from typing import Optional, Protocol
from sqlalchemy.exc import IntegrityError

from aicmo.qc.api.dtos import QcResultDTO
from aicmo.shared.ids import DraftId, QcResultId


class QcRepository(Protocol):
    """Repository interface for QC persistence."""
    
    def save_result(self, result: QcResultDTO) -> None:
        """Save a QC evaluation result."""
        ...
    
    def get_result(self, draft_id: DraftId) -> Optional[QcResultDTO]:
        """Retrieve QC result by draft ID."""
        ...
    
    def get_by_id(self, result_id: QcResultId) -> Optional[QcResultDTO]:
        """Retrieve QC result by result ID."""
        ...


class DatabaseQcRepo:
    """
    Database storage for QC results using SQLAlchemy.
    
    Session Lifecycle: Uses aicmo.core.db.get_session (same as Strategy/Production)
    Idempotency: draft_id uniqueness enforced by DB constraint
    """
    
    def __init__(self):
        # Import DB models and session here to avoid circular imports
        from aicmo.qc.internal.models import QcResultDB, QcIssueDB
        from aicmo.qc.internal.mappers import dto_to_db_result, db_to_dto_result
        from aicmo.core.db import get_session
        
        self._QcResultDB = QcResultDB
        self._QcIssueDB = QcIssueDB
        self._dto_to_db = dto_to_db_result
        self._db_to_dto = db_to_dto_result
        self._get_session = get_session
    
    def save_result(self, result: QcResultDTO) -> None:
        """
        Save QC result to database.
        
        Idempotency: If draft_id already exists, replaces existing result.
        This implements "latest evaluation wins" semantics.
        
        Commit boundary: Explicit commit after successful insert/update.
        Rollback: Automatic on exception via context manager.
        """
        with self._get_session() as session:
            # Check if result already exists for this draft
            existing = session.query(self._QcResultDB).filter_by(draft_id=result.draft_id).first()
            
            if existing:
                # Delete existing result (cascade deletes issues)
                session.delete(existing)
                session.flush()  # Ensure delete happens before insert
            
            # Create new result and issues
            result_db, issues_db = self._dto_to_db(result, self._QcResultDB, self._QcIssueDB)
            
            try:
                session.add(result_db)
                session.add_all(issues_db)
                session.commit()
            except IntegrityError as e:
                session.rollback()
                raise e
    
    def get_result(self, draft_id: DraftId) -> Optional[QcResultDTO]:
        """
        Retrieve QC result by draft ID.
        
        Returns None if no result found for draft.
        """
        with self._get_session() as session:
            result_db = (
                session.query(self._QcResultDB)
                .filter_by(draft_id=draft_id)
                .first()
            )
            
            if not result_db:
                return None
            
            return self._db_to_dto(result_db)
    
    def get_by_id(self, result_id: QcResultId) -> Optional[QcResultDTO]:
        """
        Retrieve QC result by result ID.
        
        Returns None if no result found.
        """
        with self._get_session() as session:
            result_db = session.query(self._QcResultDB).filter_by(id=result_id).first()
            
            if not result_db:
                return None
            
            return self._db_to_dto(result_db)
