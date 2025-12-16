"""Client-to-Delivery workflow implementation."""
from dataclasses import dataclass
from typing import Any, Dict
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text

from aicmo.orchestration.api.dtos import WorkflowInputDTO, SagaStepDTO, SagaResultDTO
from aicmo.orchestration.internal.saga import SagaCoordinator
from aicmo.orchestration.internal.repository import WorkflowRunRepository
from aicmo.shared.ids import SagaId, BriefId, StrategyId, DraftId, DeliveryPackageId
from backend.db.session import get_session

# Module ports
from aicmo.onboarding.api.ports import BriefNormalizePort
from aicmo.onboarding.api.dtos import DiscoveryNotesDTO
from aicmo.strategy.api.ports import StrategyGeneratePort
from aicmo.strategy.api.dtos import StrategyInputDTO
from aicmo.production.api.ports import DraftGeneratePort
from aicmo.qc.api.ports import QcEvaluatePort
from aicmo.qc.api.dtos import QcInputDTO
from aicmo.delivery.api.ports import DeliveryPackagePort


@dataclass
class WorkflowState:
    """Tracks workflow execution state."""
    workflow_run_id: str  # DB-backed run identifier for compensation scope
    brief_id: BriefId
    strategy_id: StrategyId = None
    draft_id: DraftId = None
    package_id: DeliveryPackageId = None
    qc_passed: bool = False
    compensations_applied: list[str] = None
    
    def __post_init__(self):
        if self.compensations_applied is None:
            self.compensations_applied = []


class ClientToDeliveryWorkflow:
    """
    End-to-end workflow: Client brief → Delivery package.
    
    Uses saga pattern with compensation for failure handling.
    """
    
    def __init__(
        self,
        saga_coordinator: SagaCoordinator,
        brief_normalize: BriefNormalizePort,
        strategy_generate: StrategyGeneratePort,
        draft_generate: DraftGeneratePort,
        qc_evaluate: QcEvaluatePort,
        delivery_package: DeliveryPackagePort,
    ):
        self._saga = saga_coordinator
        self._brief_normalize = brief_normalize
        self._strategy_generate = strategy_generate
        self._draft_generate = draft_generate
        self._qc_evaluate = qc_evaluate
        self._delivery_package = delivery_package
        
        # Workflow state (in-memory for Phase 3)
        self._state: Dict[str, WorkflowState] = {}
    
    def execute(self, input_dto: WorkflowInputDTO) -> SagaResultDTO:
        """
        Execute the complete client-to-delivery workflow.
        
        Steps:
        1. Normalize brief
        2. Generate strategy
        3. Generate draft
        4. QC evaluation (may fail)
        5. Create delivery package (may fail)
        
        On failure: compensate in reverse order.
        """
        saga_id = SagaId(f"workflow_{input_dto.brief_id}_{int(datetime.utcnow().timestamp())}")
        workflow_run_id = str(saga_id)
        
        # Create DB-backed workflow run for compensation tracking
        with get_session() as session:
            run_repo = WorkflowRunRepository(session)
            run_repo.create_run(
                brief_id=input_dto.brief_id,
                workflow_run_id=workflow_run_id,
                metadata={"force_qc_fail": input_dto.force_qc_fail}
            )
            session.commit()
        
        # Initialize state with workflow_run_id
        state = WorkflowState(
            workflow_run_id=workflow_run_id,
            brief_id=input_dto.brief_id
        )
        self._state[saga_id] = state
        
        # Register saga actions
        self._register_actions(saga_id, input_dto.force_qc_fail)
        
        # Define saga steps
        steps = [
            SagaStepDTO(
                step_name="normalize_brief",
                action="normalize_brief",
                compensation_action="compensate_brief",
                inputs={"brief_id": input_dto.brief_id},
            ),
            SagaStepDTO(
                step_name="generate_strategy",
                action="generate_strategy",
                compensation_action="compensate_strategy",
                inputs={"saga_id": saga_id},
            ),
            SagaStepDTO(
                step_name="generate_draft",
                action="generate_draft",
                compensation_action="compensate_draft",
                inputs={"saga_id": saga_id},
            ),
            SagaStepDTO(
                step_name="qc_evaluate",
                action="qc_evaluate",
                compensation_action="compensate_qc",
                inputs={"saga_id": saga_id, "force_fail": input_dto.force_qc_fail},
            ),
            SagaStepDTO(
                step_name="create_package",
                action="create_package",
                compensation_action="compensate_package",
                inputs={"saga_id": saga_id},
            ),
        ]
        
        # Execute saga
        result = self._saga.start_saga(saga_id, steps)
        
        # Update workflow_run status based on result
        with get_session() as session:
            run_repo = WorkflowRunRepository(session)
            if result.success:
                run_repo.update_status(
                    workflow_run_id=workflow_run_id,
                    status="COMPLETED",
                    completed_at=datetime.now(timezone.utc)
                )
            else:
                # Check if compensation was applied
                is_compensated = len(result.compensated_steps) > 0
                run_repo.update_status(
                    workflow_run_id=workflow_run_id,
                    status="COMPENSATED" if is_compensated else "FAILED",
                    error=f"Failed at step: {result.completed_steps[-1] if result.completed_steps else 'unknown'}"
                )
            session.commit()
        
        return result
    
    def get_state(self, saga_id: SagaId) -> WorkflowState:
        """Get workflow state for inspection."""
        return self._state.get(saga_id)
    
    def _register_actions(self, saga_id: SagaId, force_qc_fail: bool):
        """Register all action handlers for this workflow."""
        state = self._state[saga_id]
        
        def normalize_brief(inputs: dict) -> dict:
            # Call onboarding port
            discovery = DiscoveryNotesDTO(
                notes="Initial discovery call notes",
                call_date=datetime.utcnow(),
            )
            brief = self._brief_normalize.normalize_brief(inputs["brief_id"], discovery)
            return {"brief_id": brief.brief_id}
        
        def compensate_brief(inputs: dict) -> dict:
            # HARD DELETE: Remove onboarding brief and intake from database
            with get_session() as session:
                try:
                    # Delete in reverse dependency order (intake first, then brief)
                    session.execute(
                        text("DELETE FROM onboarding_intake WHERE brief_id = :brief_id"),
                        {"brief_id": str(state.brief_id)}
                    )
                    session.execute(
                        text("DELETE FROM onboarding_brief WHERE id = :brief_id"),
                        {"brief_id": str(state.brief_id)}
                    )
                    session.commit()
                    state.compensations_applied.append("brief_deleted")
                except Exception as e:
                    session.rollback()
                    # Idempotent: if already deleted, that's fine
                    state.compensations_applied.append(f"brief_delete_attempted")
            return {}
        
        def generate_strategy(inputs: dict) -> dict:
            # Call strategy port
            strategy_input = StrategyInputDTO(brief_id=state.brief_id)
            strategy = self._strategy_generate.generate(state.brief_id, strategy_input)
            state.strategy_id = strategy.strategy_id
            return {"strategy_id": strategy.strategy_id}
        
        def compensate_strategy(inputs: dict) -> dict:
            # HARD DELETE: Remove strategy document from database
            if not state.strategy_id:
                return {}
            
            with get_session() as session:
                try:
                    session.execute(
                        text("DELETE FROM strategy_document WHERE id = :strategy_id"),
                        {"strategy_id": str(state.strategy_id)}
                    )
                    session.commit()
                    state.compensations_applied.append(f"strategy_{state.strategy_id}_deleted")
                except Exception as e:
                    session.rollback()
                    state.compensations_applied.append(f"strategy_delete_attempted")
            
            # Don't clear state.strategy_id - keep for debugging
            return {}
        
        def generate_draft(inputs: dict) -> dict:
            # Call production port
            draft = self._draft_generate.generate_draft(state.strategy_id)
            state.draft_id = draft.draft_id
            return {"draft_id": draft.draft_id}
        
        def compensate_draft(inputs: dict) -> dict:
            # HARD DELETE: Remove production drafts, bundles, and assets from database
            if not state.draft_id:
                return {}
            
            with get_session() as session:
                try:
                    # Delete in reverse dependency order (deepest children first)
                    # 1. Get bundle_id(s) for this draft
                    result = session.execute(
                        text("SELECT bundle_id FROM production_bundles WHERE draft_id = :draft_id"),
                        {"draft_id": str(state.draft_id)}
                    )
                    bundle_ids = [row[0] for row in result.fetchall()]
                    
                    # 2. Delete assets (deepest children)
                    for bundle_id in bundle_ids:
                        session.execute(
                            text("DELETE FROM production_bundle_assets WHERE bundle_id = :bundle_id"),
                            {"bundle_id": bundle_id}
                        )
                    
                    # 3. Delete bundles (children)
                    session.execute(
                        text("DELETE FROM production_bundles WHERE draft_id = :draft_id"),
                        {"draft_id": str(state.draft_id)}
                    )
                    
                    # 4. Delete drafts (parents)
                    session.execute(
                        text("DELETE FROM production_drafts WHERE draft_id = :draft_id"),
                        {"draft_id": str(state.draft_id)}
                    )
                    
                    session.commit()
                    state.compensations_applied.append(f"draft_{state.draft_id}_deleted")
                except Exception as e:
                    session.rollback()
                    state.compensations_applied.append(f"draft_delete_attempted")
            
            # Don't clear state.draft_id - keep for other compensations that need it
            return {}
        
        def qc_evaluate(inputs: dict) -> dict:
            # Call QC port
            qc_input = QcInputDTO(
                draft_id=state.draft_id,
                benchmark_ids=["FORCE_FAIL"] if inputs["force_fail"] else [],
            )
            qc_result = self._qc_evaluate.evaluate(qc_input)
            
            if not qc_result.passed:
                # QC failed - cleanup the QC result row it created before raising
                with get_session() as session:
                    try:
                        # Delete QC issues first
                        session.execute(
                            text("DELETE FROM qc_issues WHERE result_id = :result_id"),
                            {"result_id": str(qc_result.result_id)}
                        )
                        # Delete QC result
                        session.execute(
                            text("DELETE FROM qc_results WHERE id = :result_id"),
                            {"result_id": str(qc_result.result_id)}
                        )
                        session.commit()
                    except Exception:
                        session.rollback()
                
                raise Exception(f"QC failed with score {qc_result.score}")
            
            state.qc_passed = True
            return {"qc_result_id": qc_result.result_id}
        
        def compensate_qc(inputs: dict) -> dict:
            # HARD DELETE: Remove QC results and issues from database
            # Use draft_id from state (should still be set during compensation)
            draft_id_for_cleanup = state.draft_id
            if not draft_id_for_cleanup:
                # Already compensated or never created
                state.compensations_applied.append("qc_delete_skipped")
                return {}
            
            with get_session() as session:
                try:
                    # Delete QC data associated with this draft
                    # 1. Get qc_result_id(s) for this draft
                    result = session.execute(
                        text("SELECT id FROM qc_results WHERE draft_id = :draft_id"),
                        {"draft_id": str(draft_id_for_cleanup)}
                    )
                    qc_result_ids = [row[0] for row in result.fetchall()]
                    
                    # 2. Delete issues first (children)
                    for result_id in qc_result_ids:
                        session.execute(
                            text("DELETE FROM qc_issues WHERE result_id = :result_id"),
                            {"result_id": result_id}
                        )
                    
                    # 3. Delete results (parents)
                    session.execute(
                        text("DELETE FROM qc_results WHERE draft_id = :draft_id"),
                        {"draft_id": str(draft_id_for_cleanup)}
                    )
                    
                    session.commit()
                    state.compensations_applied.append("qc_evaluation_deleted")
                except Exception as e:
                    session.rollback()
                    state.compensations_applied.append("qc_delete_attempted")
            
            # Don't clear state.qc_passed here - keep state intact for debugging
            return {}
        
        def create_package(inputs: dict) -> dict:
            # Call delivery port
            package = self._delivery_package.create_package(state.draft_id)
            state.package_id = package.package_id
            return {"package_id": package.package_id}
        
        def compensate_package(inputs: dict) -> dict:
            # HARD DELETE: Remove delivery package and artifacts from database
            if not state.package_id:
                return {}
            
            with get_session() as session:
                try:
                    # Delete in reverse dependency order (children first)
                    # 1. Delete artifacts (children)
                    session.execute(
                        text("DELETE FROM delivery_artifacts WHERE package_id = :package_id"),
                        {"package_id": str(state.package_id)}
                    )
                    
                    # 2. Delete packages (parents)
                    session.execute(
                        text("DELETE FROM delivery_packages WHERE id = :package_id"),
                        {"package_id": str(state.package_id)}
                    )
                    
                    session.commit()
                    state.compensations_applied.append(f"package_{state.package_id}_deleted")
                except Exception as e:
                    session.rollback()
                    state.compensations_applied.append(f"package_delete_attempted")
            
            # Don't clear state.package_id - keep for debugging
            return {}
        
        # Register all actions
        self._saga.register_action("normalize_brief", normalize_brief)
        self._saga.register_action("compensate_brief", compensate_brief)
        self._saga.register_action("generate_strategy", generate_strategy)
        self._saga.register_action("compensate_strategy", compensate_strategy)
        self._saga.register_action("generate_draft", generate_draft)
        self._saga.register_action("compensate_draft", compensate_draft)
        self._saga.register_action("qc_evaluate", qc_evaluate)
        self._saga.register_action("compensate_qc", compensate_qc)
        self._saga.register_action("create_package", create_package)
        self._saga.register_action("compensate_package", compensate_package)
