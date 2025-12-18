# AICMO Session State Contract - Quick Reference

**Build:** BLOCKER_FIX_2025_12_17  
**Status:** ✅ ENFORCED

---

## Canonical Session State Keys

### Active Context (Required for all downstream tabs)

```python
st.session_state["active_client_id"]      # str: UUID of active client
st.session_state["active_engagement_id"]  # str: UUID of active engagement
```

**Set by**: Intake tab after successful form submission  
**Required by**: Strategy, Creatives, Execution, Monitoring, Delivery tabs

---

## Usage Pattern

### Setting Context (Intake Tab Only)

```python
def run_intake_step(inputs: Dict[str, Any]) -> Dict[str, Any]:
    # ... validation logic ...
    
    # Create IDs via IntakeStore
    intake_store = IntakeStore(mode="inmemory")
    client_id = intake_store.create_client(intake_content)
    engagement_id = intake_store.create_engagement(client_id, intake_content)
    
    # Set canonical keys (R1 requirement)
    st.session_state["active_client_id"] = client_id
    st.session_state["active_engagement_id"] = engagement_id
    
    return {"status": "SUCCESS", ...}
```

---

### Enforcing Context (All Downstream Tabs)

```python
def run_strategy_step(inputs: Dict[str, Any]) -> Dict[str, Any]:
    # Enforce active context (blocks if missing)
    ctx = require_active_context()
    if not ctx:
        return {
            "status": "FAILED",
            "content": "⛔ Context Required: Complete Intake first",
            ...
        }
    
    client_id, engagement_id = ctx
    
    # ... rest of logic ...
```

---

## Helper Function: require_active_context()

**Location**: [operator_v2.py](operator_v2.py#L203)

**Signature**:
```python
def require_active_context() -> Optional[Tuple[str, str]]:
    """
    Enforce Active Context contract.
    
    Returns:
        (client_id, engagement_id) if both present
        None if missing (shows error + calls st.stop())
    """
```

**Behavior**:
- ✅ **Both keys present**: Returns `(client_id, engagement_id)` tuple
- ❌ **Keys missing**: Shows blocking error, calls `st.stop()`, returns `None`

**Error Message**:
```
⛔ Context Required: Complete the Intake tab first to set active client and engagement.
ℹ️ Navigate to the Intake tab, fill in the form, and click Generate to establish context.
```

---

## Tab Dependency Matrix

| Tab | Requires Context | Requires Artifacts |
|-----|------------------|-------------------|
| Intake | ❌ No | ❌ No |
| Strategy | ✅ Yes | ✅ Intake (approved) |
| Creatives | ✅ Yes | ✅ Strategy (approved) |
| Execution | ✅ Yes | ✅ Strategy + Creatives (approved) |
| Monitoring | ✅ Yes | ❌ No |
| Delivery | ✅ Yes | ❌ No |

---

## Context Lifecycle

```
┌──────────────────────────────────────────────────────────────┐
│ 1. User opens AICMO Operator Dashboard                      │
│    → st.session_state initialized (all keys = None)         │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. User navigates to Intake tab                             │
│    → Fills form with client/engagement details              │
│    → Clicks "Generate"                                       │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. run_intake_step() executes                               │
│    → Validates inputs                                        │
│    → Creates client_id + engagement_id via IntakeStore      │
│    → Sets st.session_state["active_client_id"]             │
│    → Sets st.session_state["active_engagement_id"]         │
│    → Returns SUCCESS                                         │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. User navigates to Strategy/Creatives/etc.               │
│    → Tab function calls require_active_context()            │
│    → Context present → Returns (client_id, engagement_id)   │
│    → Tab proceeds with generation                           │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 5. User switches tabs                                        │
│    → Context persists across tabs (Streamlit session state) │
│    → All tabs can access same client_id + engagement_id     │
└──────────────────────────────────────────────────────────────┘
```

---

## Error Scenarios

### Scenario 1: User Skips Intake Tab

**Behavior**:
1. User navigates directly to Strategy tab
2. Strategy tab calls `require_active_context()`
3. Keys missing → Blocking error shown
4. `st.stop()` called → Tab stops rendering
5. User sees: "⛔ Context Required: Complete the Intake tab first"

**Resolution**: Navigate to Intake tab, fill form, click Generate

---

### Scenario 2: Session State Cleared

**Behavior**:
1. User completes Intake (context set)
2. Session state cleared (browser refresh, cache clear, etc.)
3. Keys missing → Blocking error shown on next tab access

**Resolution**: Re-run Intake workflow to restore context

---

### Scenario 3: Manual Key Deletion (Dev/Debug)

**Behavior**:
1. Dev deletes keys via `st.session_state.pop("active_client_id")`
2. Next tab access → Blocking error
3. `require_active_context()` enforces contract regardless of deletion cause

**Resolution**: Re-run Intake to restore keys

---

## Testing Contract

### Unit Test: Context Missing

```python
def test_require_active_context_blocks_when_missing():
    import sys
    from unittest.mock import MagicMock
    
    mock_st = MagicMock()
    mock_st.session_state = {}  # Empty session state
    sys.modules['streamlit'] = mock_st
    
    from operator_v2 import require_active_context
    
    result = require_active_context()
    
    assert mock_st.error.called  # Error shown
    assert mock_st.stop.called   # Execution stopped
    assert result is None        # None returned
```

### Unit Test: Context Present

```python
def test_require_active_context_returns_tuple_when_present():
    import sys
    from unittest.mock import MagicMock
    
    mock_st = MagicMock()
    mock_st.session_state = {
        "active_client_id": "test-client-123",
        "active_engagement_id": "test-engagement-456"
    }
    sys.modules['streamlit'] = mock_st
    
    from operator_v2 import require_active_context
    
    result = require_active_context()
    
    assert result == ("test-client-123", "test-engagement-456")
    assert not mock_st.stop.called  # Execution continues
```

---

## Migration Guide (For Existing Tabs)

### Before (Manual Checks)

```python
def run_strategy_step(inputs: Dict[str, Any]) -> Dict[str, Any]:
    client_id = st.session_state.get("active_client_id")
    engagement_id = st.session_state.get("active_engagement_id")
    
    if not client_id or not engagement_id:
        return {
            "status": "FAILED",
            "content": "⚠️ Cannot generate strategy: No active client/engagement",
            "meta": {"tab": "strategy"},
            "debug": {}
        }
    
    # ... rest of logic ...
```

### After (Centralized Enforcer)

```python
def run_strategy_step(inputs: Dict[str, Any]) -> Dict[str, Any]:
    ctx = require_active_context()
    if not ctx:
        return {
            "status": "FAILED",
            "content": "⛔ Context Required: Complete Intake first",
            "meta": {"tab": "strategy"},
            "debug": {}
        }
    
    client_id, engagement_id = ctx
    
    # ... rest of logic ...
```

**Benefits**:
- ✅ Consistent error messages across all tabs
- ✅ Single source of truth for context enforcement
- ✅ Easier to test (mock one function instead of many)
- ✅ Cleaner code (3 lines instead of 8)

---

## Debugging Tips

### Check Context State

```python
# In any tab, add temporary debug output
st.write("Debug: Context State")
st.write(f"active_client_id: {st.session_state.get('active_client_id')}")
st.write(f"active_engagement_id: {st.session_state.get('active_engagement_id')}")
```

### Verify Context Set

```python
# After Intake submission, verify keys are set
if "active_client_id" in st.session_state:
    st.success(f"✅ Context Active: {st.session_state['active_client_id']}")
else:
    st.error("❌ Context NOT set after Intake")
```

### Test Context Enforcement

```python
# Manually test blocking behavior
del st.session_state["active_client_id"]  # Simulate missing key
ctx = require_active_context()  # Should show error + stop
st.write("This line should not render")  # Will not execute
```

---

## API Reference

### Session State Keys

| Key | Type | Set By | Required By | Description |
|-----|------|--------|-------------|-------------|
| `active_client_id` | str (UUID) | Intake | All downstream | Canonical client identifier |
| `active_engagement_id` | str (UUID) | Intake | All downstream | Canonical engagement identifier |

### Functions

#### `require_active_context() -> Optional[Tuple[str, str]]`

**Purpose**: Enforce Active Context contract for downstream tabs

**Returns**:
- `(client_id, engagement_id)` if both keys present
- `None` if keys missing (shows error, calls `st.stop()`)

**Raises**: Never (handles errors internally via st.error + st.stop)

**Side Effects**:
- Shows blocking error message if keys missing
- Calls `st.stop()` to halt tab rendering if keys missing

**Usage**:
```python
ctx = require_active_context()
if not ctx:
    return {"status": "FAILED", ...}

client_id, engagement_id = ctx
```

---

## Compliance Checklist

- ✅ R0: Single source of truth for validation (validate_intake alias)
- ✅ R1: Single Active Context contract (require_active_context enforcer)
- ✅ R3: No silent failures (structured JSON returns)
- ✅ R4: No import shadowing (single artifact_store.py verified)

---

**Last Updated**: 2025-12-17  
**Build Tag**: BLOCKER_FIX_2025_12_17  
**Status**: ✅ PRODUCTION READY
