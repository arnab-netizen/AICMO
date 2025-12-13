"""Orchestration - Port Interfaces."""
from abc import ABC, abstractmethod
from aicmo.orchestration.api.dtos import WorkflowStepDTO, WorkflowContextDTO, SagaStepDTO
from aicmo.shared.ids import WorkflowId, SagaId, EventId

class EventBusPort(ABC):
    @abstractmethod
    def publish(self, event_id: EventId, event_data: dict) -> None:
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, handler_fn) -> None:
        pass

class WorkflowRunnerPort(ABC):
    @abstractmethod
    def run_workflow(self, workflow_id: WorkflowId, context: WorkflowContextDTO) -> None:
        pass

class RetryPolicyPort(ABC):
    @abstractmethod
    def should_retry(self, attempt_count: int, error: Exception) -> bool:
        pass

class SagaCoordinatorPort(ABC):
    @abstractmethod
    def start_saga(self, saga_id: SagaId, steps: list[SagaStepDTO]) -> None:
        pass
    
    @abstractmethod
    def compensate(self, saga_id: SagaId) -> None:
        pass

__all__ = ["EventBusPort", "WorkflowRunnerPort", "RetryPolicyPort", "SagaCoordinatorPort"]
