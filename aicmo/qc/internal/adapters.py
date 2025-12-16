"""QC module - Internal adapters (MVP)."""
from datetime import datetime
from aicmo.qc.api.ports import QcEvaluatePort, QcQueryPort
from aicmo.qc.api.dtos import QcInputDTO, QcResultDTO, QcIssueDTO
from aicmo.shared.ids import DraftId, QcResultId
from aicmo.qc.internal.repositories_mem import InMemoryQcRepo


class QcEvaluateAdapter(QcEvaluatePort):
    """Minimal QC evaluation adapter."""
    
    def __init__(self, repo: InMemoryQcRepo, pass_threshold: float = 0.7):
        self._repo = repo
        self._pass_threshold = pass_threshold
    
    def evaluate(self, input_data: QcInputDTO) -> QcResultDTO:
        """
        Evaluate draft quality.
        
        MVP: Deterministic scoring based on simple rules.
        Can be configured to pass/fail for testing compensation.
        """
        result_id = QcResultId(f"qc_{input_data.draft_id}_{int(datetime.utcnow().timestamp())}")
        
        # Simulate QC evaluation
        issues = []
        score = 0.85  # Default passing score
        
        # For testing: can inject failure via benchmark_ids
        if "FORCE_FAIL" in input_data.benchmark_ids:
            score = 0.50
            issues.append(
                QcIssueDTO(
                    severity="critical",
                    section="content",
                    reason="Failed quality threshold for testing",
                )
            )
        
        result = QcResultDTO(
            result_id=result_id,
            draft_id=input_data.draft_id,
            passed=(score >= self._pass_threshold),
            score=score,
            issues=issues,
            evaluated_at=datetime.utcnow(),
        )
        
        self._repo.save_result(result)
        return result


class QcQueryAdapter(QcQueryPort):
    """Minimal query adapter."""
    
    def __init__(self, repo: InMemoryQcRepo):
        self._repo = repo
    
    def get_result(self, draft_id: DraftId) -> QcResultDTO:
        result = self._repo.get_result(draft_id)
        if not result:
            raise ValueError(f"QC result for draft {draft_id} not found")
        return result
