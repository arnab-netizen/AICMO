"""E2E DB-Mode Compensation Verification - Delivery Failure.

This test suite proves that Saga compensation works against real DB state
when the final step (Delivery) fails.

Hard Rules:
- AICMO_PERSISTENCE_MODE=db must be set
- All DB assertions must query actual database
- Verify full workflow DB state is cleaned on delivery failure
"""
import pytest
from aicmo.orchestration.composition.root import get_composition_root, reset_composition_root
from aicmo.orchestration.internal.workflows.client_to_delivery import ClientToDeliveryWorkflow
from aicmo.orchestration.api.dtos import WorkflowInputDTO
from aicmo.shared.ids import ClientId, BriefId
from aicmo.shared.config import is_db_mode
from aicmo.core.db import get_session
from aicmo.delivery.internal.adapters import DeliveryPackageAdapter

# DB Models
from aicmo.onboarding.internal.models import BriefDB
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
def workflow_with_delivery_failure(require_db_mode):
    """Create workflow where delivery fails (DB mode, custom failing adapter)."""
    reset_composition_root()
    root = get_composition_root()
    
    # Create a failing delivery adapter
    class FailingDeliveryAdapter(DeliveryPackageAdapter):
        def create_package(self, draft_id):
            raise Exception("Delivery system unavailable")
    
    # Replace delivery adapter with failing one
    delivery_package = FailingDeliveryAdapter(root._delivery_repo)
    
    # Proof: verify DB repositories are in use
    from aicmo.production.internal.repositories_db import DatabaseProductionRepo
    from aicmo.qc.internal.repositories_db import DatabaseQcRepo
    
    assert isinstance(root._production_repo, DatabaseProductionRepo), \
        f"Expected DatabaseProductionRepo, got {type(root._production_repo).__name__}"
    assert isinstance(root._qc_repo, DatabaseQcRepo), \
        f"Expected DatabaseQcRepo, got {type(root._qc_repo).__name__}"
    
    # Create workflow with failing delivery
    return ClientToDeliveryWorkflow(
        saga_coordinator=root.saga_coordinator,
        brief_normalize=root.brief_normalize,
        strategy_generate=root.strategy_generate,
        draft_generate=root.draft_generate,
        qc_evaluate=root.qc_evaluate,
        delivery_package=delivery_package,
    )


def count_db_rows(session, model_class):
    """Query DB and return row count for given model."""
    return session.query(model_class).count()


def test_delivery_fail_db_full_compensation(workflow_with_delivery_failure, cleanup_db_for_e2e):
    """CRITICAL: Verify ALL DB rows cleaned when delivery fails (full compensation chain)."""
    # Arrange
    input_dto = WorkflowInputDTO(
        client_id=ClientId("client_del_db"),
        brief_id=BriefId("brief_del_db"),
        force_qc_fail=False,  # QC must pass
    )
    
    # Act - all steps up to delivery succeed, then delivery fails
    result = workflow_with_delivery_failure.execute(input_dto)
    
    # Assert workflow failed at delivery
    assert result.success is False
    assert "qc_evaluate" in result.completed_steps  # QC passed
    assert "create_package" not in result.completed_steps  # Delivery failed
    
    # CRITICAL DB VERIFICATION: Query actual database after full compensation
    with get_session() as session:
        brief_count = count_db_rows(session, BriefDB)
        strategy_count = count_db_rows(session, StrategyDocumentDB)
        draft_count = count_db_rows(session, ContentDraftDB)
        qc_count = count_db_rows(session, QcResultDB)
        qc_issues_count = count_db_rows(session, QcIssueDB)
        delivery_count = count_db_rows(session, DeliveryPackageDB)
        artifacts_count = count_db_rows(session, DeliveryArtifactDB)
        
        print(f"\n=== DB STATE AFTER DELIVERY FAILURE + FULL COMPENSATION ===")
        print(f"BriefDB rows: {brief_count}")
        print(f"StrategyDocumentDB rows: {strategy_count}")
        print(f"ContentDraftDB rows: {draft_count}")
        print(f"QcResultDB rows: {qc_count}")
        print(f"QcIssueDB rows: {qc_issues_count}")
        print(f"DeliveryPackageDB rows: {delivery_count}")
        print(f"DeliveryArtifactDB rows: {artifacts_count}")
        
        # ASSERTION: Complete compensation chain must clean ALL tables
        assert brief_count == 0, \
            f"Expected 0 brief rows after full compensation, found {brief_count} (compensation incomplete!)"
        assert strategy_count == 0, \
            f"Expected 0 strategy rows after full compensation, found {strategy_count} (compensation incomplete!)"
        assert draft_count == 0, \
            f"Expected 0 draft rows after full compensation, found {draft_count} (compensation incomplete!)"
        assert qc_count == 0, \
            f"Expected 0 QC rows after full compensation, found {qc_count} (compensation incomplete!)"
        assert qc_issues_count == 0, \
            f"Expected 0 QC issues after full compensation, found {qc_issues_count} (cascade failed!)"
        assert delivery_count == 0, \
            f"Expected 0 delivery rows (delivery never completed), found {delivery_count}"
        assert artifacts_count == 0, \
            f"Expected 0 artifacts (delivery never completed), found {artifacts_count}"


def test_delivery_fail_db_qc_reverted(workflow_with_delivery_failure, cleanup_db_for_e2e):
    """Verify QC results are properly reverted when delivery fails."""
    # Arrange
    input_dto = WorkflowInputDTO(
        client_id=ClientId("client_qc_revert"),
        brief_id=BriefId("brief_qc_revert"),
    )
    
    # Act
    result = workflow_with_delivery_failure.execute(input_dto)
    
    # Assert
    assert result.success is False
    assert "qc_evaluate" in result.completed_steps  # QC initially passed
    assert "qc_evaluate" in result.compensated_steps  # Then reverted
    
    # CRITICAL: Verify QC data removed from DB
    with get_session() as session:
        qc_count = count_db_rows(session, QcResultDB)
        qc_issues_count = count_db_rows(session, QcIssueDB)
        
        print(f"\n=== QC REVERSION VERIFICATION ===")
        print(f"QcResultDB rows after compensation: {qc_count}")
        print(f"QcIssueDB rows after compensation: {qc_issues_count}")
        
        # QC compensation must delete QC results from DB
        assert qc_count == 0, \
            f"QC compensation failed: {qc_count} QC result rows remain in DB"
        assert qc_issues_count == 0, \
            f"QC cascade failed: {qc_issues_count} QC issue rows remain in DB"


def test_delivery_fail_db_compensation_order(workflow_with_delivery_failure, cleanup_db_for_e2e):
    """Verify compensation happens in reverse order (LIFO)."""
    # Arrange
    input_dto = WorkflowInputDTO(
        client_id=ClientId("client_order"),
        brief_id=BriefId("brief_order"),
    )
    
    # Act
    result = workflow_with_delivery_failure.execute(input_dto)
    
    # Assert compensation order
    assert result.success is False
    compensated = result.compensated_steps
    
    # Order must be reverse of execution:
    # Forward: brief → strategy → draft → qc
    # Reverse: qc → draft → strategy → brief
    qc_idx = compensated.index("qc_evaluate")
    draft_idx = compensated.index("generate_draft")
    strategy_idx = compensated.index("generate_strategy")
    brief_idx = compensated.index("normalize_brief")
    
    print(f"\n=== COMPENSATION ORDER VERIFICATION ===")
    print(f"Compensated steps: {compensated}")
    print(f"Indices: QC={qc_idx}, Draft={draft_idx}, Strategy={strategy_idx}, Brief={brief_idx}")
    
    # QC compensated before draft, draft before strategy, strategy before brief
    assert qc_idx < draft_idx, "QC must compensate before draft"
    assert draft_idx < strategy_idx, "Draft must compensate before strategy"
    assert strategy_idx < brief_idx, "Strategy must compensate before brief"
    
    # DB must be clean regardless of order
    with get_session() as session:
        total_rows = (
            count_db_rows(session, BriefDB) +
            count_db_rows(session, StrategyDocumentDB) +
            count_db_rows(session, ContentDraftDB) +
            count_db_rows(session, QcResultDB) +
            count_db_rows(session, DeliveryPackageDB)
        )
        
        print(f"Total DB rows after compensation: {total_rows}")
        assert total_rows == 0, \
            f"Compensation left {total_rows} orphan rows in DB (order issue?)"


def test_delivery_fail_db_idempotency(workflow_with_delivery_failure, cleanup_db_for_e2e):
    """Verify multiple delivery failures don't accumulate orphan data."""
    # Arrange
    input_dto = WorkflowInputDTO(
        client_id=ClientId("client_idem"),
        brief_id=BriefId("brief_idem"),
    )
    
    # Act - Execute multiple times
    result1 = workflow_with_delivery_failure.execute(input_dto)
    result2 = workflow_with_delivery_failure.execute(input_dto)
    result3 = workflow_with_delivery_failure.execute(input_dto)
    
    # Assert all failed
    assert result1.success is False
    assert result2.success is False
    assert result3.success is False
    
    # CRITICAL: DB must be clean (no accumulation)
    with get_session() as session:
        brief_count = count_db_rows(session, BriefDB)
        strategy_count = count_db_rows(session, StrategyDocumentDB)
        draft_count = count_db_rows(session, ContentDraftDB)
        qc_count = count_db_rows(session, QcResultDB)
        delivery_count = count_db_rows(session, DeliveryPackageDB)
        
        print(f"\n=== DB STATE AFTER 3 DELIVERY FAILURES ===")
        print(f"Brief: {brief_count}, Strategy: {strategy_count}, Draft: {draft_count}")
        print(f"QC: {qc_count}, Delivery: {delivery_count}")
        
        # No orphan data from repeated failures
        assert brief_count == 0, f"Orphan brief data after 3 failures: {brief_count}"
        assert strategy_count == 0, f"Orphan strategy data after 3 failures: {strategy_count}"
        assert draft_count == 0, f"Orphan draft data after 3 failures: {draft_count}"
        assert qc_count == 0, f"Orphan QC data after 3 failures: {qc_count}"
        assert delivery_count == 0, f"Orphan delivery data after 3 failures: {delivery_count}"


def test_delivery_fail_db_concurrent_workflows(workflow_with_delivery_failure, cleanup_db_for_e2e):
    """Verify compensation doesn't affect other successful workflows."""
    # Arrange - Create successful workflow first
    reset_composition_root()
    root = get_composition_root()
    success_workflow = root.create_client_to_delivery_workflow()
    
    success_input = WorkflowInputDTO(
        client_id=ClientId("client_success_concurrent"),
        brief_id=BriefId("brief_success_concurrent"),
    )
    success_result = success_workflow.execute(success_input)
    assert success_result.success is True
    
    # Capture successful workflow's DB state
    with get_session() as session:
        success_brief_count = count_db_rows(session, BriefDB)
        success_delivery_count = count_db_rows(session, DeliveryPackageDB)
    
    # Act - Execute failing workflow
    fail_input = WorkflowInputDTO(
        client_id=ClientId("client_fail_concurrent"),
        brief_id=BriefId("brief_fail_concurrent"),
    )
    fail_result = workflow_with_delivery_failure.execute(fail_input)
    assert fail_result.success is False
    
    # CRITICAL: Successful workflow data must be preserved
    with get_session() as session:
        final_brief_count = count_db_rows(session, BriefDB)
        final_delivery_count = count_db_rows(session, DeliveryPackageDB)
        
        print(f"\n=== CONCURRENT WORKFLOW ISOLATION ===")
        print(f"Brief rows: {success_brief_count} → {final_brief_count}")
        print(f"Delivery rows: {success_delivery_count} → {final_delivery_count}")
        
        # Failed workflow compensation must not touch successful workflow data
        assert final_brief_count == success_brief_count, \
            "Delivery failure compensation deleted unrelated brief data!"
        assert final_delivery_count == success_delivery_count, \
            "Delivery failure compensation deleted unrelated delivery data!"
