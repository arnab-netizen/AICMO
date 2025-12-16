"""
QC module mappers - DTO ↔ DB model conversion.

Handles serialization/deserialization of QC results and issues.
"""

from datetime import datetime, timezone
from typing import List

from aicmo.qc.api.dtos import QcResultDTO, QcIssueDTO
from aicmo.shared.ids import QcResultId, DraftId


def dto_to_db_result(dto: QcResultDTO, result_db_class, issue_db_class):
    """
    Convert QcResultDTO to database models.
    
    Returns tuple: (QcResultDB, List[QcIssueDB])
    """
    now = datetime.now(timezone.utc)
    
    result_db = result_db_class(
        id=dto.result_id,
        draft_id=dto.draft_id,
        passed=dto.passed,
        score=dto.score,
        evaluated_at=dto.evaluated_at,
        created_at=now,
        updated_at=now,
    )
    
    issues_db = [
        issue_db_class(
            result_id=dto.result_id,
            severity=issue.severity,
            section=issue.section,
            reason=issue.reason,
            created_at=now,
        )
        for issue in dto.issues
    ]
    
    return result_db, issues_db


def db_to_dto_result(result_db) -> QcResultDTO:
    """Convert QcResultDB (with loaded issues) to QcResultDTO."""
    issues = [
        QcIssueDTO(
            severity=issue.severity,
            section=issue.section,
            reason=issue.reason,
        )
        for issue in result_db.issues
    ]
    
    return QcResultDTO(
        result_id=QcResultId(result_db.id),
        draft_id=DraftId(result_db.draft_id),
        passed=result_db.passed,
        score=result_db.score,
        issues=issues,
        evaluated_at=result_db.evaluated_at,
    )
