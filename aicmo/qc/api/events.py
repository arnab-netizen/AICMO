"""QC - Events."""
from aicmo.shared.events import DomainEvent
from aicmo.shared.ids import DraftId, QcResultId

class QcPassed(DomainEvent):
    result_id: QcResultId
    draft_id: DraftId
    score: float

class QcFailed(DomainEvent):
    result_id: QcResultId
    draft_id: DraftId
    issue_count: int

__all__ = ["QcPassed", "QcFailed"]
