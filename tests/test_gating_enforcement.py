import pytest

from aicmo.domain.state_machine import ProjectState, can_transition
from aicmo.ui import gating


def test_require_state_blocks_illegal():
    with pytest.raises(gating.IllegalStateTransitionError):
        gating.require_state(ProjectState.CREATED, ProjectState.STRATEGY_GENERATED, "do_strategy")


def test_strategy_approved_cannot_regress_without_override():
    # cannot move backwards without override
    with pytest.raises(gating.IllegalStateTransitionError):
        gating.require_state(ProjectState.STRATEGY_APPROVED, ProjectState.CREATED, "regress_test")


def test_qc_failed_blocks_delivered():
    with pytest.raises(gating.IllegalStateTransitionError):
        gating.require_state(ProjectState.QC_FAILED, ProjectState.DELIVERED, "deliver")


def test_override_allows_transition_once():
    # illegal transition normally blocked
    with pytest.raises(gating.IllegalStateTransitionError):
        gating.require_state(ProjectState.CREATED, ProjectState.STRATEGY_GENERATED, "action")

    # register override
    gating.require_override("force test", "tester")

    # now override should allow
    gating.require_state(ProjectState.CREATED, ProjectState.STRATEGY_GENERATED, "action")

    # second attempt should be blocked again
    with pytest.raises(gating.IllegalStateTransitionError):
        gating.require_state(ProjectState.CREATED, ProjectState.STRATEGY_GENERATED, "action")
