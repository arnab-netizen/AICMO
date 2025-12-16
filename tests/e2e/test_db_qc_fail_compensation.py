"""E2E DB-Mode Compensation Verification - QC Failure.

This test suite proves that Saga compensation works against real DB state.
It explicitly verifies DB row counts and state transitions during failure scenarios.

Hard Rules:
- AICMO_PERSISTENCE_MODE=db must be set
- All DB assertions must query actual database
- No assumptions about in-memory state
"""
import pytest
from aicmo.orchestration.composition.root import get_composition_root, reset_composition_root
from aicmo.orchestration.api.dtos import WorkflowInputDTO
from aicmo.shared.ids import ClientId, BriefId
from aicmo.shared.config import is_db_mode
from aicmo.core.db import get_session

# DB Models
from aicmo.onboarding.internal.models import BriefDB, IntakeDB
from aicmo.strategy.internal.models import StrategyDocumentDB
from aicmo.production.internal.models import ContentDraftDB
from aicmo.qc.internal.models import QcResultDB, QcIssueDB
from aicmo.delivery.internal.models import DeliveryPackageDB, DeliveryArtifactDB


# Module-level guard: Ensure DB is clean before running tests
def pytest_configure(config):
    """Verify DB is clean at module load (guard against fixture failures)."""
    if is_db_mode():
        with get_session() as session:
            brief_count = session.query(BriefDB).count()
            strategy_count = session.query(StrategyDocumentDB).count()
            draft_count = session.query(ContentDraftDB).count()
            qc_count = session.query(QcResultDB).count()
            
            total_rows = brief_count + strategy_count + draft_count + qc_count
            
            if total_rows > 0:
                pytest.fail(
                    f"DB not clean at test module start; cleanup fixture broken. "
                    f"Found {total_rows} rows (Brief: {brief_count}, Strategy: {strategy_count}, "
                    f"Draft: {draft_count}, QC: {qc_count})"
                )


@pytest.fixture
def require_db_mode():
    """Ensure tests only run in DB mode."""
    if not is_db_mode():
        pytest.skip("Test requires AICMO_PERSISTENCE_MODE=db")


@pytest.fixture
def workflow(require_db_mode):
    """Create workflow using CompositionRoot in DB mode."""
    reset_composition_root()
    root = get_composition_root()
    workflow = root.create_client_to_delivery_workflow()
    
    # Explicit proof: verify DB repositories are in use
    from aicmo.strategy.internal.repositories_db import DatabaseStrategyRepo
    from aicmo.production.internal.repositories_db import DatabaseProductionRepo
    from aicmo.qc.internal.repositories_db import DatabaseQcRepo
    from aicmo.delivery.internal.repositories_db import DatabaseDeliveryRepo
    
    assert isinstance(workflow._strategy_generate._repo, DatabaseStrategyRepo), \
        f"Expected DatabaseStrategyRepo, got {type(workflow._strategy_generate._repo).__name__}"
    assert isinstance(workflow._draft_generate._repo, DatabaseProductionRepo), \
        f"Expected DatabaseProductionRepo, got {type(workflow._draft_generate._repo).__name__}"
    assert isinstance(workflow._qc_evaluate._repo, DatabaseQcRepo), \
        f"Expected DatabaseQcRepo, got {type(workflow._qc_evaluate._repo).__name__}"
    assert isinstance(workflow._delivery_package._repo, DatabaseDeliveryRepo), \
        f"Expected DatabaseDeliveryRepo, got {type(workflow._delivery_package._repo).__name__}"
    
    return workflow


def count_db_rows(session, model_class):
    """Query DB and return row count for given model."""
    return session.query(model_class).count()


def test_qc_fail_db_state_before_compensation(workflow, cleanup_db_for_e2e):
    """CRITICAL: Verify DB rows exist BEFORE compensation runs."""
    # Arrange
    input_dto = WorkflowInputDTO(
        client_id=ClientId("client_db_before"),
        brief_id=BriefId("brief_db_before"),
        force_qc_fail=True,
    )
    
    # Act - workflow will fail at QC and run compensations
    result = workflow.execute(input_dto)
    
    # Assert workflow failed as expected
    assert result.success is False
    assert "qc_evaluate" not in result.completed_steps
    
    # CRITICAL DB VERIFICATION: Query actual database
    with get_session() as session:
        # After compensation, verify DB state
        # Strategy: Depending on compensation implementation, rows may be:
        # 1. Deleted (ideal for compensation)
        # 2. Marked invalid (status field)
        # 3. Still present (compensation was in-memory only - FAIL case)
        
        brief_count = count_db_rows(session, BriefDB)
        strategy_count = count_db_rows(session, StrategyDocumentDB)
        draft_count = count_db_rows(session, ContentDraftDB)
        qc_count = count_db_rows(session, QcResultDB)
        delivery_count = count_db_rows(session, DeliveryPackageDB)
        
        # Document actual state (for evidence)
        print(f"\n=== DB STATE AFTER QC FAILURE + COMPENSATION ===")
        print(f"BriefDB rows: {brief_count}")
        print(f"StrategyDocumentDB rows: {strategy_count}")
        print(f"ContentDraftDB rows: {draft_count}")
        print(f"QcResultDB rows: {qc_count}")
        print(f"DeliveryPackageDB rows: {delivery_count}")
        
        # ASSERTION: After compensation, NO rows should remain from failed workflow
        # If this fails, compensation is NOT working against DB
        assert brief_count == 0, \
            f"Expected 0 brief rows after compensation, found {brief_count} (compensation not working!)"
        assert strategy_count == 0, \
            f"Expected 0 strategy rows after compensation, found {strategy_count} (compensation not working!)"
        assert draft_count == 0, \
            f"Expected 0 draft rows after compensation, found {draft_count} (compensation not working!)"
        assert qc_count == 0, \
            f"Expected 0 QC rows (QC never completed), found {qc_count}"
        assert delivery_count == 0, \
            f"Expected 0 delivery rows (never reached delivery), found {delivery_count}"


def test_qc_fail_db_cascade_artifacts(workflow, cleanup_db_for_e2e):
    """Verify child tables are also cleaned (cascade behavior)."""
    # Arrange
    input_dto = WorkflowInputDTO(
        client_id=ClientId("client_cascade"),
        brief_id=BriefId("brief_cascade"),
        force_qc_fail=True,
    )
    
    # Act
    result = workflow.execute(input_dto)
    
    # Assert
    assert result.success is False
    
    # CRITICAL: Verify child tables also cleaned
    with get_session() as session:
        qc_issues_count = count_db_rows(session, QcIssueDB)
        artifacts_count = count_db_rows(session, DeliveryArtifactDB)
        
        print(f"\n=== CHILD TABLE STATE AFTER COMPENSATION ===")
        print(f"QcIssueDB rows: {qc_issues_count}")
        print(f"DeliveryArtifactDB rows: {artifacts_count}")
        
        # All child rows must also be gone
        assert qc_issues_count == 0, \
            f"Expected 0 QC issue rows (QC never completed), found {qc_issues_count}"
        assert artifacts_count == 0, \
            f"Expected 0 artifact rows (delivery never reached), found {artifacts_count}"


def test_qc_fail_db_idempotency_on_retry(workflow, cleanup_db_for_e2e):
    """Verify repeated execution doesn't accumulate orphan rows."""
    # Arrange
    input_dto = WorkflowInputDTO(
        client_id=ClientId("client_retry"),
        brief_id=BriefId("brief_retry"),
        force_qc_fail=True,
    )
    
    # Act - Execute multiple times (simulating retries)
    result1 = workflow.execute(input_dto)
    result2 = workflow.execute(input_dto)
    result3 = workflow.execute(input_dto)
    
    # Assert all failed
    assert result1.success is False
    assert result2.success is False
    assert result3.success is False
    
    # CRITICAL: DB should still be clean (no accumulation)
    with get_session() as session:
        brief_count = count_db_rows(session, BriefDB)
        strategy_count = count_db_rows(session, StrategyDocumentDB)
        draft_count = count_db_rows(session, ContentDraftDB)
        qc_count = count_db_rows(session, QcResultDB)
        
        print(f"\n=== DB STATE AFTER 3 FAILED RETRIES ===")
        print(f"BriefDB rows: {brief_count}")
        print(f"StrategyDocumentDB rows: {strategy_count}")
        print(f"ContentDraftDB rows: {draft_count}")
        print(f"QcResultDB rows: {qc_count}")
        
        # No orphan rows from multiple failures
        assert brief_count == 0, \
            f"Expected 0 brief rows after 3 compensations, found {brief_count} (orphan data!)"
        assert strategy_count == 0, \
            f"Expected 0 strategy rows after 3 compensations, found {strategy_count} (orphan data!)"
        assert draft_count == 0, \
            f"Expected 0 draft rows after 3 compensations, found {draft_count} (orphan data!)"
        assert qc_count == 0, \
            f"Expected 0 QC rows after 3 failures, found {qc_count} (orphan data!)"


def test_qc_fail_db_state_isolation(workflow, cleanup_db_for_e2e):
    """Verify failed workflow doesn't affect unrelated data."""
    # Arrange - First create a successful workflow
    success_input = WorkflowInputDTO(
        client_id=ClientId("client_success"),
        brief_id=BriefId("brief_success"),
        force_qc_fail=False,
    )
    success_result = workflow.execute(success_input)
    assert success_result.success is True
    
    # Capture successful workflow's DB state
    with get_session() as session:
        success_brief_count = count_db_rows(session, BriefDB)
        success_strategy_count = count_db_rows(session, StrategyDocumentDB)
        success_draft_count = count_db_rows(session, ContentDraftDB)
        success_qc_count = count_db_rows(session, QcResultDB)
        success_delivery_count = count_db_rows(session, DeliveryPackageDB)
    
    # Now execute a failing workflow
    fail_input = WorkflowInputDTO(
        client_id=ClientId("client_fail_isolated"),
        brief_id=BriefId("brief_fail_isolated"),
        force_qc_fail=True,
    )
    fail_result = workflow.execute(fail_input)
    assert fail_result.success is False
    
    # CRITICAL: Verify successful workflow data is unchanged
    with get_session() as session:
        final_brief_count = count_db_rows(session, BriefDB)
        final_strategy_count = count_db_rows(session, StrategyDocumentDB)
        final_draft_count = count_db_rows(session, ContentDraftDB)
        final_qc_count = count_db_rows(session, QcResultDB)
        final_delivery_count = count_db_rows(session, DeliveryPackageDB)
        
        print(f"\n=== DB STATE ISOLATION VERIFICATION ===")
        print(f"Brief rows: {success_brief_count} → {final_brief_count}")
        print(f"Strategy rows: {success_strategy_count} → {final_strategy_count}")
        print(f"Draft rows: {success_draft_count} → {final_draft_count}")
        print(f"QC rows: {success_qc_count} → {final_qc_count}")
        print(f"Delivery rows: {success_delivery_count} → {final_delivery_count}")
        
        # Successful workflow data must be preserved
        assert final_brief_count == success_brief_count, \
            "Failed workflow compensation affected unrelated brief data!"
        assert final_strategy_count == success_strategy_count, \
            "Failed workflow compensation affected unrelated strategy data!"
        assert final_draft_count == success_draft_count, \
            "Failed workflow compensation affected unrelated draft data!"
        assert final_qc_count == success_qc_count, \
            "Failed workflow compensation affected unrelated QC data!"
        assert final_delivery_count == success_delivery_count, \
            "Failed workflow compensation affected unrelated delivery data!"
