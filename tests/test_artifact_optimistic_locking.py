import pytest
from aicmo.domain.artifacts import Artifact, ArtifactType, ArtifactStatus, QualityContract
from aicmo.ui.persistence.artifact_store import ArtifactStore, ConflictError


def make_qc():
    return QualityContract(
        artifact_type="CREATIVES",
        required_depth=1,
        required_specificity=1,
        required_metrics={},
        anti_generic_score=0.5,
        passes_semantic_qc=True,
    )


def test_two_writers_conflict():
    store = ArtifactStore(session_state={})

    base = Artifact(
        id="a2",
        tenant_id="t1",
        project_id="p2",
        type=ArtifactType.CREATIVES,
        status=ArtifactStatus.DRAFT,
        schema_version="1.0",
        version=1,
        produced_by="system",
        produced_at="2025-01-01T00:00:00Z",
        input_artifact_ids=[],
        state_at_creation="CREATED",
        trace_id="tr2",
        created_by="operator",
        checksum="def",
        quality_contract=make_qc(),
        content={"x": 1},
    )

    store.put(base)

    # Writer A reads latest (v1) and will attempt to write expecting v1
    # Writer B advances to v2
    b = base.copy()
    b.version = 2
    b.content = {"x": 2}
    store.put(b, expected_version=1)

    # Now writer A tries to put expecting v1 -> should get ConflictError
    a_attempt = base.copy()
    a_attempt.content = {"x": 3}
    with pytest.raises(ConflictError):
        store.put(a_attempt, expected_version=1)
