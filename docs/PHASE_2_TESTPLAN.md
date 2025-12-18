# PHASE 2 TEST PLAN

1. Allowed transitions to test

- CREATED -> INTAKE_COMPLETE
- INTAKE_COMPLETE -> STRATEGY_GENERATED
- STRATEGY_GENERATED -> STRATEGY_APPROVED
- STRATEGY_APPROVED -> CAMPAIGN_DEFINED
- CAMPAIGN_DEFINED -> CREATIVE_GENERATED
- CREATIVE_GENERATED -> QC_FAILED
- CREATIVE_GENERATED -> QC_APPROVED
- QC_FAILED -> QC_APPROVED
- QC_APPROVED -> DELIVERED

2. Illegal transitions to test (examples)

- CREATED -> STRATEGY_GENERATED
- INTAKE_COMPLETE -> STRATEGY_APPROVED
- STRATEGY_APPROVED -> CREATED
- CREATIVE_GENERATED -> STRATEGY_APPROVED
- QC_APPROVED -> CREATED
- DELIVERED -> CREATED
- DELIVERED -> QC_APPROVED
- STRATEGY_GENERATED -> DELIVERED
- INTAKE_COMPLETE -> CREATIVE_GENERATED
- QC_FAILED -> DELIVERED

3. Override behavior tests

- Attempt illegal transition, call `require_override(reason, actor)`, then perform transition — must succeed once.
- Second identical illegal transition attempt without new override must fail.

4. Failure expectations

- Illegal transitions must be blocked by `require_state` raising `IllegalStateTransitionError`.
- `can_transition` must return False for illegal transitions.
