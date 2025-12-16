"""
QC module in-memory repository.

Implements QC result persistence using in-memory dictionaries.
Mirrors DatabaseQcRepo interface for dual-mode support.
"""

from typing import Dict, Optional

from aicmo.qc.api.dtos import QcResultDTO
from aicmo.shared.ids import DraftId, QcResultId


class InMemoryQcRepo:
    """In-memory storage for QC results."""
    
    def __init__(self):
        self._results: Dict[QcResultId, QcResultDTO] = {}
        self._by_draft: Dict[DraftId, QcResultId] = {}
    
    def save_result(self, result: QcResultDTO) -> None:
        """
        Save QC result to in-memory storage.
        
        Idempotency: If draft_id already exists, replaces existing result.
        Same semantics as DatabaseQcRepo.
        """
        # Remove old result for this draft if exists
        if result.draft_id in self._by_draft:
            old_result_id = self._by_draft[result.draft_id]
            if old_result_id in self._results:
                del self._results[old_result_id]
        
        # Save new result
        self._results[result.result_id] = result
        self._by_draft[result.draft_id] = result.result_id
    
    def get_result(self, draft_id: DraftId) -> Optional[QcResultDTO]:
        """
        Retrieve QC result by draft ID.
        
        Returns None if no result found for draft.
        Returns a copy to prevent mutation of stored data.
        """
        result_id = self._by_draft.get(draft_id)
        if result_id:
            result = self._results.get(result_id)
            if result:
                # Return copy to prevent mutation
                return QcResultDTO(
                    result_id=result.result_id,
                    draft_id=result.draft_id,
                    passed=result.passed,
                    score=result.score,
                    issues=result.issues.copy(),  # Copy list
                    evaluated_at=result.evaluated_at,
                )
        return None
    
    def get_by_id(self, result_id: QcResultId) -> Optional[QcResultDTO]:
        """
        Retrieve QC result by result ID.
        
        Returns None if no result found.
        Returns a copy to prevent mutation of stored data.
        """
        result = self._results.get(result_id)
        if result:
            # Return copy to prevent mutation
            return QcResultDTO(
                result_id=result.result_id,
                draft_id=result.draft_id,
                passed=result.passed,
                score=result.score,
                issues=result.issues.copy(),  # Copy list
                evaluated_at=result.evaluated_at,
            )
        return None
