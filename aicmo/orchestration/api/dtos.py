"""Orchestration - DTOs."""
from pydantic import BaseModel
from typing import Dict, Any, Optional
from aicmo.shared.ids import WorkflowId, SagaId

class WorkflowStepDTO(BaseModel):
    step_name: str
    action: str
    inputs: Dict[str, Any]
    retry_config: Dict[str, Any] = {}

class WorkflowContextDTO(BaseModel):
    workflow_id: WorkflowId
    context_data: Dict[str, Any]
    current_step: Optional[str] = None

class SagaStepDTO(BaseModel):
    step_name: str
    action: str
    compensation_action: str
    inputs: Dict[str, Any]

class SagaResultDTO(BaseModel):
    saga_id: SagaId
    success: bool
    completed_steps: list[str]
    compensated_steps: list[str] = []

__all__ = ["WorkflowStepDTO", "WorkflowContextDTO", "SagaStepDTO", "SagaResultDTO"]
