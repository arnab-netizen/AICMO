import inspect


def test_canonical_projectstate_only():
    import aicmo.domain.state_machine as sm
    import aicmo.domain.project as proj

    # Canonical ProjectState must exist in state_machine
    assert hasattr(sm, "ProjectState"), "Canonical ProjectState missing in state_machine"
    # If project exposes ProjectState, it must be the canonical one (imported), not a duplicate
    assert getattr(proj, "ProjectState", None) is sm.ProjectState


def test_qc_approved_present():
    import aicmo.domain.state_machine as sm
    assert hasattr(sm.ProjectState, "QC_APPROVED"), "QC_APPROVED must be present in canonical ProjectState"
