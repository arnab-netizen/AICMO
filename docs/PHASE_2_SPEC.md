# PHASE 2 SPEC — ProjectState and Transitions

1. ProjectState enum values

- CREATED
- INTAKE_COMPLETE
- STRATEGY_GENERATED
- STRATEGY_APPROVED
- CAMPAIGN_DEFINED
- CREATIVE_GENERATED
- QC_FAILED
- QC_APPROVED
- DELIVERED

2. Legal transitions table

| From | To |
|------|----|
| CREATED | INTAKE_COMPLETE |
| INTAKE_COMPLETE | STRATEGY_GENERATED |
| STRATEGY_GENERATED | STRATEGY_APPROVED |
| STRATEGY_APPROVED | CAMPAIGN_DEFINED |
| CAMPAIGN_DEFINED | CREATIVE_GENERATED |
| CREATIVE_GENERATED | QC_FAILED |
| CREATIVE_GENERATED | QC_APPROVED |
| QC_FAILED | QC_APPROVED |
| QC_APPROVED | DELIVERED |

3. Illegal transition rule

- Any transition not listed in the Legal transitions table is illegal.
- No implicit multi-step transitions allowed (e.g., cannot go CREATED -> STRATEGY_GENERATED directly).

4. Override rule

- An explicit override may allow a single attempted illegal transition to proceed once.
- Overrides are in-memory only and are not persisted by Phase 2.
- Overrides must be recorded via `require_override(reason: str, actor: str)` and consumed by the gating layer.

5. Invariants

- State values are authoritative and atomic.
- `can_transition(from_state, to_state)` is a pure function with no side effects.
- Gating enforcement raises `IllegalStateTransitionError` with action_name, current_state, required_state.
