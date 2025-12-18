import pytest

from aicmo.domain.state_machine import ProjectState, can_transition


def test_legal_transitions_true():
    legal = [
        (ProjectState.CREATED, ProjectState.INTAKE_COMPLETE),
        (ProjectState.INTAKE_COMPLETE, ProjectState.STRATEGY_GENERATED),
        (ProjectState.STRATEGY_GENERATED, ProjectState.STRATEGY_APPROVED),
        (ProjectState.STRATEGY_APPROVED, ProjectState.CAMPAIGN_DEFINED),
        (ProjectState.CAMPAIGN_DEFINED, ProjectState.CREATIVE_GENERATED),
        (ProjectState.CREATIVE_GENERATED, ProjectState.QC_FAILED),
        (ProjectState.CREATIVE_GENERATED, ProjectState.QC_APPROVED),
        (ProjectState.QC_FAILED, ProjectState.QC_APPROVED),
        (ProjectState.QC_APPROVED, ProjectState.DELIVERED),
    ]
    for frm, to in legal:
        assert can_transition(frm, to), f"Expected allowed: {frm} -> {to}"


def test_illegal_transitions_false():
    illegal = [
        (ProjectState.CREATED, ProjectState.STRATEGY_GENERATED),
        (ProjectState.INTAKE_COMPLETE, ProjectState.STRATEGY_APPROVED),
        (ProjectState.STRATEGY_APPROVED, ProjectState.CREATED),
        (ProjectState.CREATIVE_GENERATED, ProjectState.STRATEGY_APPROVED),
        (ProjectState.QC_APPROVED, ProjectState.CREATED),
        (ProjectState.DELIVERED, ProjectState.CREATED),
        (ProjectState.DELIVERED, ProjectState.QC_APPROVED),
        (ProjectState.STRATEGY_GENERATED, ProjectState.DELIVERED),
        (ProjectState.INTAKE_COMPLETE, ProjectState.CREATIVE_GENERATED),
        (ProjectState.QC_FAILED, ProjectState.DELIVERED),
    ]
    for frm, to in illegal:
        assert not can_transition(frm, to), f"Expected illegal: {frm} -> {to}"
