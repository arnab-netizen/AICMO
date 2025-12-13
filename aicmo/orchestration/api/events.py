"""Orchestration - Events."""
from aicmo.shared.events import DomainEvent
from aicmo.shared.ids import WorkflowId, SagaId

class WorkflowStarted(DomainEvent):
    workflow_id: WorkflowId

class WorkflowStepSucceeded(DomainEvent):
    workflow_id: WorkflowId
    step_name: str

class WorkflowStepFailed(DomainEvent):
    workflow_id: WorkflowId
    step_name: str
    error_message: str

class WorkflowCompleted(DomainEvent):
    workflow_id: WorkflowId

__all__ = ["WorkflowStarted", "WorkflowStepSucceeded", "WorkflowStepFailed", "WorkflowCompleted"]
