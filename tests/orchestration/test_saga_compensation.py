"""Tests for SagaCoordinator - Compensation logic."""
import pytest
from aicmo.orchestration.internal.saga import SagaCoordinator
from aicmo.orchestration.api.dtos import SagaStepDTO
from aicmo.shared.ids import SagaId


def test_saga_compensates_on_failure():
    """Test that saga runs compensations when a step fails."""
    coordinator = SagaCoordinator()
    
    executed_actions = []
    state = {"created_resources": []}
    
    def action_a(inputs: dict) -> dict:
        executed_actions.append("action_a")
        state["created_resources"].append("resource_a")
        return {"resource": "resource_a"}
    
    def action_b(inputs: dict) -> dict:
        executed_actions.append("action_b")
        state["created_resources"].append("resource_b")
        return {"resource": "resource_b"}
    
    def action_c_fails(inputs: dict) -> dict:
        executed_actions.append("action_c_fails")
        raise Exception("Step C failed!")
    
    def compensate_a(inputs: dict) -> dict:
        executed_actions.append("compensate_a")
        state["created_resources"].remove("resource_a")
        return {}
    
    def compensate_b(inputs: dict) -> dict:
        executed_actions.append("compensate_b")
        state["created_resources"].remove("resource_b")
        return {}
    
    def compensate_c(inputs: dict) -> dict:
        executed_actions.append("compensate_c")
        return {}
    
    coordinator.register_action("action_a", action_a)
    coordinator.register_action("action_b", action_b)
    coordinator.register_action("action_c_fails", action_c_fails)
    coordinator.register_action("compensate_a", compensate_a)
    coordinator.register_action("compensate_b", compensate_b)
    coordinator.register_action("compensate_c", compensate_c)
    
    steps = [
        SagaStepDTO(step_name="step_a", action="action_a", compensation_action="compensate_a", inputs={}),
        SagaStepDTO(step_name="step_b", action="action_b", compensation_action="compensate_b", inputs={}),
        SagaStepDTO(step_name="step_c", action="action_c_fails", compensation_action="compensate_c", inputs={}),
    ]
    
    result = coordinator.start_saga(SagaId("saga_fail"), steps)
    
    # Saga failed
    assert result.success is False
    assert result.completed_steps == ["step_a", "step_b"]
    assert result.compensated_steps == ["step_b", "step_a"]
    
    # Verify execution order: forward steps, then compensations in reverse
    assert executed_actions == [
        "action_a",
        "action_b",
        "action_c_fails",
        "compensate_b",  # reverse order
        "compensate_a",
    ]
    
    # State was rolled back
    assert len(state["created_resources"]) == 0


def test_saga_compensates_in_reverse_order():
    """Test that compensations run in reverse order of execution."""
    coordinator = SagaCoordinator()
    
    compensation_order = []
    
    def action_1(inputs: dict) -> dict:
        return {}
    
    def action_2(inputs: dict) -> dict:
        return {}
    
    def action_3_fails(inputs: dict) -> dict:
        raise Exception("Failure at step 3")
    
    def compensate_1(inputs: dict) -> dict:
        compensation_order.append(1)
        return {}
    
    def compensate_2(inputs: dict) -> dict:
        compensation_order.append(2)
        return {}
    
    def compensate_3(inputs: dict) -> dict:
        compensation_order.append(3)
        return {}
    
    coordinator.register_action("action_1", action_1)
    coordinator.register_action("action_2", action_2)
    coordinator.register_action("action_3_fails", action_3_fails)
    coordinator.register_action("compensate_1", compensate_1)
    coordinator.register_action("compensate_2", compensate_2)
    coordinator.register_action("compensate_3", compensate_3)
    
    steps = [
        SagaStepDTO(step_name="s1", action="action_1", compensation_action="compensate_1", inputs={}),
        SagaStepDTO(step_name="s2", action="action_2", compensation_action="compensate_2", inputs={}),
        SagaStepDTO(step_name="s3", action="action_3_fails", compensation_action="compensate_3", inputs={}),
    ]
    
    coordinator.start_saga(SagaId("saga_reverse"), steps)
    
    # Compensations ran in reverse: 2, then 1 (step 3 never completed)
    assert compensation_order == [2, 1]


def test_saga_compensation_changes_state():
    """Test that compensations actually change state (not no-ops)."""
    coordinator = SagaCoordinator()
    
    # Track state changes
    app_state = {
        "users_created": [],
        "orders_created": [],
    }
    
    def create_user(inputs: dict) -> dict:
        user_id = inputs["user_id"]
        app_state["users_created"].append(user_id)
        return {"user_id": user_id}
    
    def create_order(inputs: dict) -> dict:
        # Fail before modifying state
        raise Exception("Payment failed")
    
    def delete_user(inputs: dict) -> dict:
        user_id = inputs["user_id"]
        app_state["users_created"].remove(user_id)
        return {}
    
    def delete_order(inputs: dict) -> dict:
        # This shouldn't run since create_order failed
        order_id = inputs["order_id"]
        if order_id in app_state["orders_created"]:
            app_state["orders_created"].remove(order_id)
        return {}
    
    coordinator.register_action("create_user", create_user)
    coordinator.register_action("create_order", create_order)
    coordinator.register_action("delete_user", delete_user)
    coordinator.register_action("delete_order", delete_order)
    
    steps = [
        SagaStepDTO(
            step_name="user",
            action="create_user",
            compensation_action="delete_user",
            inputs={"user_id": "user_123"}
        ),
        SagaStepDTO(
            step_name="order",
            action="create_order",
            compensation_action="delete_order",
            inputs={"order_id": "order_456"}
        ),
    ]
    
    result = coordinator.start_saga(SagaId("saga_state"), steps)
    
    # Saga failed
    assert result.success is False
    
    # User was created then deleted (state changed by compensation)
    assert len(app_state["users_created"]) == 0
    assert len(app_state["orders_created"]) == 0


def test_saga_manual_compensation_call():
    """Test manually calling compensate on an existing saga."""
    coordinator = SagaCoordinator()
    
    compensations_run = []
    
    def action_a(inputs: dict) -> dict:
        return {}
    
    def action_b(inputs: dict) -> dict:
        return {}
    
    def compensate_a(inputs: dict) -> dict:
        compensations_run.append("a")
        return {}
    
    def compensate_b(inputs: dict) -> dict:
        compensations_run.append("b")
        return {}
    
    coordinator.register_action("action_a", action_a)
    coordinator.register_action("action_b", action_b)
    coordinator.register_action("compensate_a", compensate_a)
    coordinator.register_action("compensate_b", compensate_b)
    
    steps = [
        SagaStepDTO(step_name="step_a", action="action_a", compensation_action="compensate_a", inputs={}),
        SagaStepDTO(step_name="step_b", action="action_b", compensation_action="compensate_b", inputs={}),
    ]
    
    saga_id = SagaId("saga_manual")
    result = coordinator.start_saga(saga_id, steps)
    
    # First run succeeded
    assert result.success is True
    assert len(compensations_run) == 0
    
    # Now manually compensate
    comp_result = coordinator.compensate(saga_id)
    
    assert comp_result.success is False
    assert comp_result.compensated_steps == ["step_b", "step_a"]
    assert compensations_run == ["b", "a"]


def test_saga_failure_at_first_step():
    """Test failure at the very first step (no compensations needed)."""
    coordinator = SagaCoordinator()
    
    compensations_run = []
    
    def action_fails(inputs: dict) -> dict:
        raise Exception("First step fails")
    
    def compensate_1(inputs: dict) -> dict:
        compensations_run.append("compensate_1")
        return {}
    
    coordinator.register_action("action_fails", action_fails)
    coordinator.register_action("compensate_1", compensate_1)
    
    steps = [
        SagaStepDTO(step_name="s1", action="action_fails", compensation_action="compensate_1", inputs={}),
    ]
    
    result = coordinator.start_saga(SagaId("saga_first_fail"), steps)
    
    assert result.success is False
    assert result.completed_steps == []
    assert result.compensated_steps == []
    # No compensations run because no steps completed
    assert len(compensations_run) == 0
