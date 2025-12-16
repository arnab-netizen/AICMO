"""
Manual test to verify HARD DELETE compensation is working.
"""
from aicmo.orchestration.composition.root import get_composition_root, reset_composition_root
from aicmo.orchestration.api.dtos import WorkflowInputDTO
from aicmo.shared.ids import ClientId, BriefId
from aicmo.core.db import get_session
from aicmo.onboarding.internal.models import BriefDB
from aicmo.strategy.internal.models import StrategyDocumentDB
from aicmo.production.internal.models import ContentDraftDB
from aicmo.qc.internal.models import QcResultDB
from sqlalchemy import text

# Clean DB first
print("=== CLEANING DB ===")
with get_session() as session:
    tables = [
        'delivery_artifacts',
        'production_bundle_assets',
        'production_bundles',
        'qc_issues',
        'delivery_packages',
        'production_drafts',
        'qc_results',
        'strategy_document',
        'onboarding_intake',
        'onboarding_brief',
        'workflow_runs',
    ]
    for table in tables:
        session.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
    session.commit()
print("✅ DB cleaned")

# Count rows before
print("\n=== BEFORE WORKFLOW ===")
with get_session() as session:
    brief_before = session.query(BriefDB).count()
    strategy_before = session.query(StrategyDocumentDB).count()
    draft_before = session.query(ContentDraftDB).count()
    qc_before = session.query(QcResultDB).count()
    print(f"Briefs: {brief_before}, Strategies: {strategy_before}, Drafts: {draft_before}, QC: {qc_before}")

# Run workflow with QC failure
print("\n=== RUNNING WORKFLOW (will fail at QC) ===")
reset_composition_root()
root = get_composition_root()
workflow = root.create_client_to_delivery_workflow()

input_dto = WorkflowInputDTO(
    client_id=ClientId("test_client"),
    brief_id=BriefId("test_brief"),
    force_qc_fail=True,
)

result = workflow.execute(input_dto)

print(f"Success: {result.success}")
print(f"Completed steps: {result.completed_steps}")
print(f"Compensated steps: {result.compensated_steps}")

# Get workflow state to see what happened
state = workflow.get_state(result.saga_id)
print(f"Compensations applied: {state.compensations_applied}")

# Count rows after
print("\n=== AFTER COMPENSATION ===")
with get_session() as session:
    brief_after = session.query(BriefDB).count()
    strategy_after = session.query(StrategyDocumentDB).count()
    draft_after = session.query(ContentDraftDB).count()
    qc_after = session.query(QcResultDB).count()
    print(f"Briefs: {brief_after}, Strategies: {strategy_after}, Drafts: {draft_after}, QC: {qc_after}")

# Verify deletion
if brief_after == 0 and strategy_after == 0 and draft_after == 0 and qc_after == 0:
    print("\n✅ SUCCESS: All rows deleted via HARD DELETE compensation")
else:
    print(f"\n❌ FAILURE: Rows still remain (Briefs: {brief_after}, Strategies: {strategy_after}, Drafts: {draft_after}, QC: {qc_after})")
