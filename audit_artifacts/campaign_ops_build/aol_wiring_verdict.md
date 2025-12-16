# AOL Action Registration Pattern - VERDICT

## Finding

**Pattern**: Direct action dispatch in daemon loop + adapter functions

### Evidence

1. **AOL Daemon location**: `aicmo/orchestration/daemon.py`
   
   Action dispatch logic (lines 150-180):
   ```python
   for action in actions:
       try:
           # Dispatch action
           if action.action_type == "POST_SOCIAL":
               import json
               payload = json.loads(action.payload_json) if action.payload_json else {}
               payload["idempotency_key"] = action.idempotency_key
               handle_post_social(session, action.id, payload, proof_mode=proof_mode)
               actions_succeeded += 1
           else:
               # Unknown action type
               error_msg = f"Unknown action type: {action.action_type}"
               ActionQueue.log_execution(session, action.id, "ERROR", error_msg)
               ActionQueue.mark_failed(session, action.id, error_msg)
   ```

2. **Adapter pattern**: `aicmo/orchestration/adapters/social_adapter.py`
   
   Function signature:
   ```python
   def handle_post_social(session: Session, action_id: int, payload: Dict[str, Any], proof_mode: bool) -> None:
       # Validate payload
       # Execute action
       # Log results
   ```

3. **Action model**: `aicmo/orchestration/models.py`
   ```python
   class AOLAction(Base):
       idempotency_key = Column(String(255), unique=True)
       action_type = Column(String(100))  # ← String-based dispatch
       payload_json = Column(Text)
       status = Column(String(20))
       attempts = Column(Integer, default=0)
   ```

4. **Action Queue interface**: `aicmo/orchestration/queue.py`
   ```python
   @staticmethod
   def enqueue_action(
       session: Session,
       action_type: str,
       payload: Dict[str, Any],
       idempotency_key: Optional[str] = None,
       not_before: Optional[datetime] = None,
   ) -> AOLAction:
   ```

## Integration Strategy

### Option A: Add if-elif block to daemon (SIMPLE)

**Location**: `aicmo/orchestration/daemon.py` lines 170-180

**Modification**:
```python
# AICMO_CAMPAIGN_OPS_WIRING_START
if action.action_type == "POST_SOCIAL":
    import json
    payload = json.loads(action.payload_json) if action.payload_json else {}
    payload["idempotency_key"] = action.idempotency_key
    handle_post_social(session, action.id, payload, proof_mode=proof_mode)
    actions_succeeded += 1
elif action.action_type == "CAMPAIGN_TICK":
    from aicmo.campaign_ops.actions import handle_campaign_tick
    import json
    payload = json.loads(action.payload_json) if action.payload_json else {}
    payload["idempotency_key"] = action.idempotency_key
    handle_campaign_tick(session, action.id, payload, proof_mode=proof_mode)
    actions_succeeded += 1
elif action.action_type == "ESCALATE_OVERDUE_TASKS":
    from aicmo.campaign_ops.actions import handle_escalate_overdue
    import json
    payload = json.loads(action.payload_json) if action.payload_json else {}
    payload["idempotency_key"] = action.idempotency_key
    handle_escalate_overdue(session, action.id, payload, proof_mode=proof_mode)
    actions_succeeded += 1
elif action.action_type == "WEEKLY_CAMPAIGN_SUMMARY":
    from aicmo.campaign_ops.actions import handle_weekly_summary
    import json
    payload = json.loads(action.payload_json) if action.payload_json else {}
    payload["idempotency_key"] = action.idempotency_key
    handle_weekly_summary(session, action.id, payload, proof_mode=proof_mode)
    actions_succeeded += 1
# AICMO_CAMPAIGN_OPS_WIRING_END
else:
    # Unknown action type
    error_msg = f"Unknown action type: {action.action_type}"
    ActionQueue.log_execution(session, action.id, "ERROR", error_msg)
    ActionQueue.mark_failed(session, action.id, error_msg)
```

### Option B: Create action registry (CLEANER, for future)

Not implemented now, but future refactor option:
- Create `aicmo/orchestration/action_registry.py`
- Register handlers: `HANDLERS = {"POST_SOCIAL": handle_post_social, ...}`
- Lookup: `handler = HANDLERS.get(action.action_type, handle_unknown)`

## Required New Adapters

Create in `aicmo/orchestration/adapters/`:

1. **campaign_adapter.py**
   - `handle_campaign_tick(session, action_id, payload, proof_mode)`
   - `handle_escalate_overdue(session, action_id, payload, proof_mode)`
   - `handle_weekly_summary(session, action_id, payload, proof_mode)`

## Worker Entry Point

**Scripts**:
- `scripts/run_aol_worker.py` - Render background worker
- `scripts/run_aol_daemon.py` - Alternative daemon runner

Both use `aicmo/orchestration/daemon.py` loop. Only need to modify daemon.py once.

## No Breaking Changes

- ✅ Adding elif blocks (existing POST_SOCIAL unchanged)
- ✅ Wrapped in clear markers for future removal
- ✅ Adapters are new files
- ✅ Old action types still work

## Conclusion

**Safe to proceed** with integrating Campaign Ops actions:

1. Create `aicmo/campaign_ops/actions.py` with three handlers
2. Create `aicmo/orchestration/adapters/campaign_adapter.py` with implementations
3. Add three elif blocks to `aicmo/orchestration/daemon.py` (lines 170-200, wrapped in markers)
4. Register action types by calling `ActionQueue.enqueue_action()` from Campaign Ops service layer
