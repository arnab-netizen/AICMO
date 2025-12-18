from aicmo.domain.artifacts import Artifact, ArtifactType, ArtifactStatus, QualityContract
from aicmo.ui.persistence.artifact_store import ArtifactStore
from aicmo.core.client_ready import is_client_ready


def make_qc():
    return QualityContract(
        artifact_type="STRATEGY",
        required_depth=1,
        required_specificity=1,
        required_metrics={},
        anti_generic_score=0.5,
        passes_semantic_qc=True,
    )


def test_missing_prereq_false():
    store = ArtifactStore(session_state={})
    assert not is_client_ready("t1", "p1", store)


def test_all_prereqs_true():
    store = ArtifactStore(session_state={})
    a = Artifact(
        id="c1",
        tenant_id="t1",
        project_id="p1",
        type=ArtifactType.INTAKE,
        status=ArtifactStatus.APPROVED,
        schema_version="1.0",
        version=1,
        produced_by="system",
        produced_at="2025-01-01T00:00:00Z",
        input_artifact_ids=[],
        state_at_creation="QC_APPROVED",
        trace_id="tr",
        created_by="system",
        checksum="abc",
        quality_contract=make_qc(),
        content={},
    )
    store.put(a)
    # Add strategy and creatives
    b = a.copy()
    b.id = "c2"
    b.type = ArtifactType.STRATEGY
    store.put(b)
    c = a.copy()
    c.id = "c3"
    c.type = ArtifactType.CREATIVES
    store.put(c)

    assert is_client_ready("t1", "p1", store)
