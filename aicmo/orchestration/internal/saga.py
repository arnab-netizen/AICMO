"""Saga coordinator for distributed transactions."""
from typing import Callable, Dict, Any, List
from dataclasses import dataclass, field
from aicmo.orchestration.api.ports import SagaCoordinatorPort
from aicmo.orchestration.api.dtos import SagaStepDTO, SagaResultDTO
from aicmo.shared.ids import SagaId


@dataclass
class SagaExecution:
    """Tracks the state of a running saga."""
    saga_id: SagaId
    steps: List[SagaStepDTO]
    completed_steps: List[str] = field(default_factory=list)
    compensated_steps: List[str] = field(default_factory=list)
    current_step_index: int = 0
    failed: bool = False
    failure_reason: str = ""


class SagaCoordinator(SagaCoordinatorPort):
    """
    Coordinates saga execution with compensation logic.
    
    Rules:
    - Each step must have a compensation action
    - On failure, compensations run in reverse order
    - Compensations must change state (no-op not allowed)
    """

    def __init__(self, action_registry: Dict[str, Callable] = None):
        """
        Args:
            action_registry: Map of action names to callable functions
                            Each callable receives inputs dict and returns result dict
        """
        self._action_registry = action_registry or {}
        self._executions: Dict[SagaId, SagaExecution] = {}

    def register_action(self, action_name: str, action_fn: Callable) -> None:
        """Register an action handler."""
        self._action_registry[action_name] = action_fn

    def start_saga(self, saga_id: SagaId, steps: List[SagaStepDTO]) -> SagaResultDTO:
        """
        Execute saga steps sequentially.
        On failure, compensate completed steps in reverse order.
        
        Returns:
            SagaResultDTO with success status and step tracking
        """
        execution = SagaExecution(saga_id=saga_id, steps=steps)
        self._executions[saga_id] = execution

        try:
            # Execute forward steps
            for i, step in enumerate(steps):
                execution.current_step_index = i
                self._execute_step(step, execution)
                execution.completed_steps.append(step.step_name)

            return SagaResultDTO(
                saga_id=saga_id,
                success=True,
                completed_steps=execution.completed_steps,
                compensated_steps=[]
            )

        except Exception as e:
            # Mark as failed and compensate
            execution.failed = True
            execution.failure_reason = str(e)
            return self.compensate(saga_id)

    def compensate(self, saga_id: SagaId) -> SagaResultDTO:
        """
        Run compensation for all completed steps in reverse order.
        
        Returns:
            SagaResultDTO with compensated step list
        """
        execution = self._executions.get(saga_id)
        if not execution:
            raise ValueError(f"Saga {saga_id} not found")

        # Compensate in reverse order
        for step_name in reversed(execution.completed_steps):
            # Find the step definition
            step = next(s for s in execution.steps if s.step_name == step_name)
            self._compensate_step(step, execution)
            execution.compensated_steps.append(step_name)

        return SagaResultDTO(
            saga_id=saga_id,
            success=False,
            completed_steps=execution.completed_steps,
            compensated_steps=execution.compensated_steps
        )

    def _execute_step(self, step: SagaStepDTO, execution: SagaExecution) -> Dict[str, Any]:
        """Execute a single saga step."""
        action_fn = self._action_registry.get(step.action)
        if not action_fn:
            raise ValueError(f"Action '{step.action}' not registered")
        
        result = action_fn(step.inputs)
        return result

    def _compensate_step(self, step: SagaStepDTO, execution: SagaExecution) -> None:
        """Execute compensation for a single step."""
        compensation_fn = self._action_registry.get(step.compensation_action)
        if not compensation_fn:
            raise ValueError(f"Compensation '{step.compensation_action}' not registered")
        
        # Execute compensation
        compensation_fn(step.inputs)

    def get_execution(self, saga_id: SagaId) -> SagaExecution:
        """Get saga execution state (for testing/debugging)."""
        return self._executions.get(saga_id)
