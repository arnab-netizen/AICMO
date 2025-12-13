"""Learning - Port Interfaces."""
from abc import ABC, abstractmethod
from aicmo.learning.api.dtos import LearningEventDTO, ContextQueryDTO, ContextResultDTO, StoredArtifactDTO
from aicmo.shared.ids import ProjectId

class LearningLogPort(ABC):
    @abstractmethod
    def log_event(self, event: LearningEventDTO) -> None:
        pass

class ContextRetrievePort(ABC):
    @abstractmethod
    def retrieve(self, query: ContextQueryDTO) -> ContextResultDTO:
        pass

class ArtifactStorePort(ABC):
    @abstractmethod
    def store(self, artifact: StoredArtifactDTO) -> str:
        """Returns artifact_id."""
        pass

__all__ = ["LearningLogPort", "ContextRetrievePort", "ArtifactStorePort"]
