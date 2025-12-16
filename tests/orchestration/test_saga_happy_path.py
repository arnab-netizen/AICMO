"""Tests for SagaCoordinator - Happy path."""
import pytest
from aicmo.orchestration.internal.saga import SagaCoordinator
from aicmo.orchestration.api.dtos import SagaStepDTO
from aicmo.shared.ids import SagaId


def test_saga_happy_path_all_steps_succeed():
    """Test successful saga execution with all steps completing."""
    coordinator = SagaCoordinator()
    
    # Track execution
    executed_actions = []
    
    def action_a(inputs: dict) -> dict:
        executed_actions.append(("action_a", inputs))
        return {"status": "ok"}
    
    def action_b(inputs: dict) -> dict:
        executed_actions.append(("action_b", inputs))
        return {"status": "ok"}
    
    def compensate_a(inputs: dict) -> dict:
        executed_actions.append(("compensate_a", inputs))
        return {}
    
    def compensate_b(inputs: dict) -> dict:
        executed_actions.append(("compensate_b", inputs))
        return {}
    
    coordinator.register_action("action_a", action_a)
    coordinator.register_action("action_b", action_b)
    coordinator.register_action("compensate_a", compensate_a)
    coordinator.register_action("compensate_b", compensate_b)
    
    steps = [
        SagaStepDTO(
            step_name="step_a",
            action="action_a",
            compensation_action="compensate_a",
            inputs={"data": "a"}
        ),
        SagaStepDTO(
            step_name="step_b",
            action="action_b",
            compensation_action="compensate_b",
            inputs={"data": "b"}
        ),
    ]
    
    result = coordinator.start_saga(SagaId("saga_1"), steps)
    
    assert result.success is True
    assert result.completed_steps == ["step_a", "step_b"]
    assert result.compensated_steps == []
    
    # Only forward actions executed, no compensations
    assert len(executed_actions) == 2
    assert executed_actions[0][0] == "action_a"
    assert executed_actions[1][0] == "action_b"


def test_saga_executes_steps_in_order():
    """Test that saga steps execute in the defined order."""
    coordinator = SagaCoordinator()
    
    execution_order = []
    
    def action_1(inputs: dict) -> dict:
        execution_order.append(1)
        return {}
    
    def action_2(inputs: dict) -> dict:
        execution_order.append(2)
        return {}
    
    def action_3(inputs: dict) -> dict:
        execution_order.append(3)
        return {}
    
    def noop_compensate(inputs: dict) -> dict:
        return {}
    
    coordinator.register_action("action_1", action_1)
    coordinator.register_action("action_2", action_2)
    coordinator.register_action("action_3", action_3)
    coordinator.register_action("compensate", noop_compensate)
    
    steps = [
        SagaStepDTO(step_name="s1", action="action_1", compensation_action="compensate", inputs={}),
        SagaStepDTO(step_name="s2", action="action_2", compensation_action="compensate", inputs={}),
        SagaStepDTO(step_name="s3", action="action_3", compensation_action="compensate", inputs={}),
    ]
    
    coordinator.start_saga(SagaId("saga_order"), steps)
    
    assert execution_order == [1, 2, 3]


def test_saga_passes_inputs_to_actions():
    """Test that saga passes step inputs to action handlers."""
    coordinator = SagaCoordinator()
    
    received_inputs = []
    
    def capture_action(inputs: dict) -> dict:
        received_inputs.append(inputs)
        return {}
    
    def noop_compensate(inputs: dict) -> dict:
        return {}
    
    coordinator.register_action("capture", capture_action)
    coordinator.register_action("compensate", noop_compensate)
    
    steps = [
        SagaStepDTO(
            step_name="s1",
            action="capture",
            compensation_action="compensate",
            inputs={"key1": "value1", "count": 42}
        ),
    ]
    
    coordinator.start_saga(SagaId("saga_inputs"), steps)
    
    assert len(received_inputs) == 1
    assert received_inputs[0]["key1"] == "value1"
    assert received_inputs[0]["count"] == 42
