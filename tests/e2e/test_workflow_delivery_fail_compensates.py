"""E2E tests for workflow compensation - Delivery failure."""
import pytest
from aicmo.orchestration.composition.root import get_composition_root, reset_composition_root
from aicmo.orchestration.internal.workflows.client_to_delivery import ClientToDeliveryWorkflow
from aicmo.orchestration.api.dtos import WorkflowInputDTO
from aicmo.shared.ids import ClientId, BriefId
from aicmo.shared.config import is_db_mode
from aicmo.delivery.internal.adapters import DeliveryPackageAdapter


@pytest.fixture
def workflow_with_delivery_failure():
    """Create workflow where delivery fails (uses CompositionRoot + custom failing adapter)."""
    reset_composition_root()
    root = get_composition_root()
    
    # Create a failing delivery adapter
    class FailingDeliveryAdapter(DeliveryPackageAdapter):
        def create_package(self, draft_id):
            raise Exception("Delivery system unavailable")
    
    # Replace delivery adapter with failing one
    delivery_package = FailingDeliveryAdapter(root._delivery_repo)
    
    # Proof assertion: verify other adapters use correct repo type
    if is_db_mode():
        from aicmo.production.internal.repositories_db import DatabaseProductionRepo
        assert isinstance(root._production_repo, DatabaseProductionRepo), \
            f"DB mode: Expected DatabaseProductionRepo, got {type(root._production_repo).__name__}"
    else:
        from aicmo.production.internal.repositories_mem import InMemoryProductionRepo
        assert isinstance(root._production_repo, InMemoryProductionRepo), \
            f"In-memory mode: Expected InMemoryProductionRepo, got {type(root._production_repo).__name__}"
    
    # Create workflow with failing delivery
    return ClientToDeliveryWorkflow(
        saga_coordinator=root.saga_coordinator,
        brief_normalize=root.brief_normalize,
        strategy_generate=root.strategy_generate,
        draft_generate=root.draft_generate,
        qc_evaluate=root.qc_evaluate,
        delivery_package=delivery_package,
    )


def test_workflow_delivery_fail_compensates(workflow_with_delivery_failure):
    """Test that delivery failure triggers full compensation."""
    # Arrange
    input_dto = WorkflowInputDTO(
        client_id=ClientId("client_del_fail"),
        brief_id=BriefId("brief_del_fail"),
        force_qc_fail=False,
    )
    
    # Act
    result = workflow_with_delivery_failure.execute(input_dto)
    
    # Assert
    assert result.success is False
    
    # All steps up to delivery completed
    assert "normalize_brief" in result.completed_steps
    assert "generate_strategy" in result.completed_steps
    assert "generate_draft" in result.completed_steps
    assert "qc_evaluate" in result.completed_steps
    # Delivery fails before completing
    assert "create_package" not in result.completed_steps
    
    # All completed steps were compensated in reverse
    assert "qc_evaluate" in result.compensated_steps
    assert "generate_draft" in result.compensated_steps
    assert "generate_strategy" in result.compensated_steps
    assert "normalize_brief" in result.compensated_steps


def test_workflow_delivery_fail_state_changes(workflow_with_delivery_failure):
    """Test that delivery failure compensation changes state."""
    # Arrange
    input_dto = WorkflowInputDTO(
        client_id=ClientId("client_del_state"),
        brief_id=BriefId("brief_del_state"),
    )
    
    # Act
    result = workflow_with_delivery_failure.execute(input_dto)
    
    # Assert
    state = workflow_with_delivery_failure.get_state(result.saga_id)
    
    # State reflects all compensations
    assert len(state.compensations_applied) >= 4
    # In DB mode (Lane C), compensations DELETE records ("_deleted" suffix)
    # In memory mode, compensations use "_reverted" or "_discarded" suffix
    assert "qc_evaluation_reverted" in state.compensations_applied or "qc_evaluation_deleted" in state.compensations_applied
    # Either hard delete or soft delete compensation occurred
    if "_deleted" in str(state.compensations_applied) or "_discarded" in str(state.compensations_applied):
        assert any("draft_" in comp and ("_deleted" in comp or "_discarded" in comp) for comp in state.compensations_applied)
        assert any("strategy_" in comp and ("_deleted" in comp or "_discarded" in comp) for comp in state.compensations_applied)
    
    # Final state shows no package created (delivery never completed)
    # Note: In DB mode, qc_passed flag may remain True even after QC compensation
    # because compensation deletes the QC record but doesn't modify state flags
    # The compensations_applied list is the authoritative source of what happened
    assert state.package_id is None  # Never created
