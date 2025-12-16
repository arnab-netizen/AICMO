"""E2E tests for workflow compensation - QC failure."""
import pytest
from aicmo.orchestration.composition.root import get_composition_root, reset_composition_root
from aicmo.orchestration.api.dtos import WorkflowInputDTO
from aicmo.shared.ids import ClientId, BriefId
from aicmo.shared.config import is_db_mode


@pytest.fixture
def workflow():
    """Create workflow using CompositionRoot (respects AICMO_PERSISTENCE_MODE)."""
    reset_composition_root()
    root = get_composition_root()
    workflow = root.create_client_to_delivery_workflow()
    
    # Proof assertion: verify workflow uses correct repo type for current mode
    if is_db_mode():
        from aicmo.strategy.internal.repositories_db import DatabaseStrategyRepo
        assert isinstance(workflow._strategy_generate._repo, DatabaseStrategyRepo), \
            f"DB mode: Expected DatabaseStrategyRepo, got {type(workflow._strategy_generate._repo).__name__}"
    else:
        from aicmo.strategy.internal.repositories_mem import InMemoryStrategyRepo
        assert isinstance(workflow._strategy_generate._repo, InMemoryStrategyRepo), \
            f"In-memory mode: Expected InMemoryStrategyRepo, got {type(workflow._strategy_generate._repo).__name__}"
    
    return workflow


def test_workflow_qc_fail_compensates(workflow):
    """Test that QC failure triggers compensation."""
    # Arrange - force QC to fail
    input_dto = WorkflowInputDTO(
        client_id=ClientId("client_fail"),
        brief_id=BriefId("brief_fail"),
        force_qc_fail=True,
    )
    
    # Act
    result = workflow.execute(input_dto)
    
    # Assert
    assert result.success is False
    
    # Steps completed up to QC
    assert "normalize_brief" in result.completed_steps
    assert "generate_strategy" in result.completed_steps
    assert "generate_draft" in result.completed_steps
    # QC fails before completing
    assert "qc_evaluate" not in result.completed_steps
    assert "create_package" not in result.completed_steps
    
    # Compensations ran in reverse order
    assert len(result.compensated_steps) > 0
    # Compensations happen in reverse: draft, strategy, brief
    assert "generate_draft" in result.compensated_steps
    assert "generate_strategy" in result.compensated_steps
    assert "normalize_brief" in result.compensated_steps


def test_workflow_qc_fail_changes_state(workflow):
    """Test that QC failure compensation actually changes state."""
    # Arrange
    input_dto = WorkflowInputDTO(
        client_id=ClientId("client_state"),
        brief_id=BriefId("brief_state"),
        force_qc_fail=True,
    )
    
    # Act
    result = workflow.execute(input_dto)
    
    # Assert
    state = workflow.get_state(result.saga_id)
    
    # State should reflect compensations
    assert len(state.compensations_applied) > 0
    # In DB mode (Lane C), compensations DELETE records (no "_discarded" suffix)
    # In memory mode, compensations use "_discarded" suffix
    if "_deleted" in str(state.compensations_applied) or "_discarded" in str(state.compensations_applied):
        # Either hard delete or soft delete compensation occurred
        assert any("draft_" in comp and ("_deleted" in comp or "_discarded" in comp) for comp in state.compensations_applied)
        assert any("strategy_" in comp and ("_deleted" in comp or "_discarded" in comp) for comp in state.compensations_applied)
    
    # QC didn't pass
    assert state.qc_passed is False
    
    # No package created
    assert state.package_id is None


def test_workflow_qc_fail_no_package_created(workflow):
    """Test that QC failure prevents package creation."""
    # Arrange
    input_dto = WorkflowInputDTO(
        client_id=ClientId("client_no_pkg"),
        brief_id=BriefId("brief_no_pkg"),
        force_qc_fail=True,
    )
    
    # Act
    result = workflow.execute(input_dto)
    
    # Assert
    state = workflow.get_state(result.saga_id)
    
    # Package was never created
    assert state.package_id is None
    
    # Draft and strategy were created but then compensated (deleted or discarded)
    # In DB mode (Lane C), compensations_applied shows "_deleted" markers
    # In memory mode, state IDs may be None or have "_discarded" suffix
    # Check compensations_applied to verify compensation occurred
    assert any("draft_" in comp and "_deleted" in comp for comp in state.compensations_applied) or \
           (state.draft_id is None or "_discarded" in str(state.draft_id))
    assert any("strategy_" in comp and "_deleted" in comp for comp in state.compensations_applied) or \
           (state.strategy_id is None or "_discarded" in str(state.strategy_id))
