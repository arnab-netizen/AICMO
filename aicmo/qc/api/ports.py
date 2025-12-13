"""QC - Port Interfaces."""
from abc import ABC, abstractmethod
from aicmo.qc.api.dtos import QcInputDTO, QcResultDTO
from aicmo.shared.ids import DraftId

class QcEvaluatePort(ABC):
    @abstractmethod
    def evaluate(self, input_data: QcInputDTO) -> QcResultDTO:
        pass

class QcQueryPort(ABC):
    @abstractmethod
    def get_result(self, draft_id: DraftId) -> QcResultDTO:
        pass

__all__ = ["QcEvaluatePort", "QcQueryPort"]
