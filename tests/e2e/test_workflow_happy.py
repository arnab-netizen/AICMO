"""E2E tests for client-to-delivery workflow - Happy path."""
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
        from aicmo.onboarding.internal.adapters import DatabaseBriefRepo
        assert isinstance(workflow._brief_normalize._repo, DatabaseBriefRepo), \
            f"DB mode: Expected DatabaseBriefRepo, got {type(workflow._brief_normalize._repo).__name__}"
    else:
        from aicmo.onboarding.internal.adapters import InMemoryBriefRepo
        assert isinstance(workflow._brief_normalize._repo, InMemoryBriefRepo), \
            f"In-memory mode: Expected InMemoryBriefRepo, got {type(workflow._brief_normalize._repo).__name__}"
    
    return workflow


def test_workflow_happy_path_produces_package(workflow):
    """Test successful workflow execution produces delivery package."""
    # Arrange
    input_dto = WorkflowInputDTO(
        client_id=ClientId("client_123"),
        brief_id=BriefId("brief_456"),
        force_qc_fail=False,
    )
    
    # Act
    result = workflow.execute(input_dto)
    
    # Assert
    assert result.success is True
    assert len(result.completed_steps) == 5
    assert result.completed_steps == [
        "normalize_brief",
        "generate_strategy",
        "generate_draft",
        "qc_evaluate",
        "create_package",
    ]
    assert len(result.compensated_steps) == 0
    
    # Verify workflow state
    state = workflow.get_state(result.saga_id)
    assert state.brief_id == input_dto.brief_id
    assert state.strategy_id is not None
    assert state.draft_id is not None
    assert state.package_id is not None
    assert state.qc_passed is True
    assert len(state.compensations_applied) == 0


def test_workflow_produces_pack_output_artifacts(workflow):
    """Test that workflow generates pack output artifacts."""
    # Arrange
    input_dto = WorkflowInputDTO(
        client_id=ClientId("client_789"),
        brief_id=BriefId("brief_abc"),
    )
    
    # Act
    result = workflow.execute(input_dto)
    
    # Assert
    assert result.success is True
    
    # Get state and verify pack artifacts exist
    state = workflow.get_state(result.saga_id)
    assert state.package_id is not None
    
    # Package ID format indicates delivery artifacts were created
    assert "pkg_" in state.package_id
    assert state.draft_id in state.package_id


def test_workflow_executes_steps_in_order(workflow):
    """Test that workflow executes steps in correct order."""
    # Arrange
    input_dto = WorkflowInputDTO(
        client_id=ClientId("client_order"),
        brief_id=BriefId("brief_order"),
    )
    
    # Act
    result = workflow.execute(input_dto)
    
    # Assert - steps completed in defined order
    assert result.completed_steps[0] == "normalize_brief"
    assert result.completed_steps[1] == "generate_strategy"
    assert result.completed_steps[2] == "generate_draft"
    assert result.completed_steps[3] == "qc_evaluate"
    assert result.completed_steps[4] == "create_package"
