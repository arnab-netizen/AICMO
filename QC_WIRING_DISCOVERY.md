# QC Wiring Discovery Report

**Date**: 2025-01-18  
**Purpose**: Map current QC infrastructure and identify wiring requirements

---

## CURRENT STATE

### 1. QC Engines

**Two QC systems exist:**

#### A. Legacy: `aicmo/ui/quality/deterministic_checks.py` (867 lines)
- **Status**: ACTIVE - Used by `tests/test_quality_layer.py`
- **Function**: `run_deterministic_checks(artifact_type: str, content: Dict) -> List[QCCheck]`
- **Coverage**: INTAKE, STRATEGY, CREATIVES, EXECUTION, MONITORING, DELIVERY
- **Usage**: Called from tests but NOT from operator_v2.py
- **Decision**: **KEEP AS LEGACY** - Not currently integrated into approval flow

#### B. New: `aicmo/ui/quality/rules/` (1,390 lines)
- **Status**: COMPLETE - 29 rules, 14/14 tests passing
- **Components**:
  - `qc_registry.py`: Rule registration system
  - `qc_runner.py`: Execution engine with `run_qc_for_artifact()`
  - `qc_persistence.py`: Session state storage (NOT ArtifactStore)
  - `ruleset_v1.py`: 29 comprehensive deterministic rules
- **Coverage**: INTAKE, STRATEGY, CREATIVES, EXECUTION, MONITORING, DELIVERY
- **Usage**: NOT yet wired to operator_v2.py
- **Decision**: **USE THIS AS PRIMARY QC ENGINE**

**RESOLUTION**: Migrate from session-state persistence to ArtifactStore-based persistence for enforcement.

---

### 2. QC Persistence (Current)

**Session State Approach** (`aicmo/ui/quality/rules/qc_persistence.py`):
```python
def save_qc_result(store, qc_artifact, client_id, engagement_id, source_artifact_id):
    # Stores in session_state with key: qc_{artifact_type}_{engagement_id}
    key = f"qc_{qc_artifact.target_artifact_type}_{engagement_id}"
    store.session_state[key] = qc_data

def load_latest_qc(store, artifact_type, engagement_id) -> Optional[QCArtifact]:
    # Retrieves from session state
    key = f"qc_{artifact_type}_{engagement_id}"
    return store.session_state.get(key)
```

**PROBLEM**: Session state lookup is NOT version-locked to target artifact. Cannot enforce "QC for version X" requirement.

**SOLUTION REQUIRED**: Migrate to ArtifactStore with version-locked keys.

---

### 3. ArtifactStore Current State

**File**: `aicmo/ui/persistence/artifact_store.py` (1,185 lines)

**ArtifactType Enum** (Lines 41-49):
```python
class ArtifactType(str, Enum):
    INTAKE = "intake"
    STRATEGY = "strategy"
    CREATIVES = "creatives"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    DELIVERY = "delivery"
    CAMPAIGN = "campaign"
    LEADGEN_REQUIREMENTS = "leadgen_requirements"
```

**QC Gate Already Exists** (Lines 622-681):
```python
def _check_qc_gate(self, artifact: Artifact) -> Tuple[bool, List[str]]:
    """
    Enforce QC gate: artifact cannot be approved without passing QC.
    
    Rules:
        1. QC artifact must exist for this artifact_id + version
        2. QC artifact target_version must match artifact.version
        3. QC status must not be FAIL
    """
```

**QC Storage Methods Already Exist** (Lines 595-620):
```python
def store_qc_artifact(self, qc_artifact) -> None:
    """Store QC artifact in session state"""
    if "_qc_artifacts" not in self.session_state:
        self.session_state["_qc_artifacts"] = {}
    
    key = f"{qc_artifact.target_artifact_id}_v{qc_artifact.target_version}"
    self.session_state["_qc_artifacts"][key] = qc_artifact.to_dict()

def get_qc_for_artifact(self, artifact: Artifact):
    """Get QC artifact for given artifact."""
    if "_qc_artifacts" not in self.session_state:
        return None
    
    key = f"{artifact.artifact_id}_v{artifact.version}"
    qc_data = self.session_state["_qc_artifacts"].get(key)
```

**approve_artifact() Already Calls QC Gate** (Lines 477-479):
```python
# NEW: Enforce QC gate - no approval without passing QC
qc_ok, qc_errors = self._check_qc_gate(artifact)
if not qc_ok:
    raise ArtifactValidationError(qc_errors, [])
```

**STATUS**: QC enforcement infrastructure EXISTS but is NOT CONNECTED to QC generation.

---

### 4. QC Integration Status

**What Works**:
- ✅ QC gate enforcement exists in `approve_artifact()`
- ✅ QC storage/retrieval methods exist in ArtifactStore
- ✅ Version-locked keys: `{artifact_id}_v{version}`
- ✅ QC rules engine complete with 29 rules

**What's Missing**:
- ❌ QC is NEVER generated/stored (no calls to `store_qc_artifact()`)
- ❌ operator_v2.py does NOT call QC generation
- ❌ No QC UI panels to display results
- ❌ No "Run QC" buttons in operator_v2.py
- ❌ No auto-QC on draft save/generate/revise

**Result**: Approval gate will ALWAYS FAIL because QC artifacts are never created.

---

## OPERATOR_V2 INTEGRATION POINTS

### Approval Flow (Lines 1606-1650)

**Current Code**:
```python
if st.button("👍 Approve Deliverable", ...):
    # ARTIFACT ENFORCEMENT: Call ArtifactStore.approve_artifact() FIRST
    try:
        approved_artifact = artifact_store.approve_artifact(
            latest_artifact,
            approved_by=st.session_state.get("operator_id", "operator")
        )
        st.success("✅ Artifact approved!")
    except ArtifactValidationError as e:
        st.error(f"❌ Approval blocked: {e.errors[0]}")
        for error in e.errors[1:]:
            st.warning(error)
```

**Wiring Needed**:
- Before approval attempt, display QC status
- If QC missing, show "Run QC" button
- If QC FAIL, show failed checks with evidence

---

### Draft Save/Generate Flows

**Locations in operator_v2.py**:

1. **Intake Tab** (Lines 1923-2050): Generate button
2. **Strategy Tab** (Lines 3000-3100): Generate button
3. **Creatives Tab** (Lines 4348-4450): Save Draft button
4. **Execution Tab** (Lines 5262-5370): Save Draft button
5. **Monitoring Tab** (Lines 5748-5850): Save Draft button
6. **Delivery Tab** (Lines 6387-6500): Generate Package button

**Wiring Needed**: After artifact save/update, call QC generation service.

---

### Existing "Run QC Checks" Buttons

**Found**:
- Line 4447: Strategy tab
- Line 4861: Creatives tab
- Line 5369: Execution tab
- Line 5848: Monitoring tab

**Status**: Buttons exist but do NOT call any QC logic. Placeholders only.

---

## IMPLEMENTATION APPROACH

### Option A: Add QC Types to ArtifactType Enum ❌

**Rejected**: Would pollute artifact type enum with non-content artifacts.

### Option B: Use Separate QC Storage in Session State ✅ **CURRENT**

**Status**: Already implemented in ArtifactStore:
```python
self.session_state["_qc_artifacts"][key] = qc_artifact.to_dict()
```

**Key Format**: `{artifact_id}_v{version}` (version-locked)

**Decision**: **USE EXISTING IMPLEMENTATION** - No changes needed to ArtifactStore structure.

---

## QC CONTENT CONTRACT

**From `aicmo/ui/quality/qc_models.py`** (verified):

```python
@dataclass
class QCArtifact:
    qc_artifact_id: str
    qc_type: QCType  # Enum: INTAKE_QC, STRATEGY_QC, etc.
    target_artifact_id: str
    target_artifact_type: str  # "intake", "strategy", etc.
    target_version: int
    qc_status: QCStatus  # PASS, WARN, FAIL
    qc_score: int  # 0-100
    checks: List[QCCheck]
    summary: QCSummary  # blockers, majors, minors counts
    model_used: Optional[str]
    created_at: str
```

**All required fields present** ✅

---

## FILES TO MODIFY

### Phase 1: QC Service (NEW FILE)

**Create**: `aicmo/ui/quality/qc_service.py`

**Functions**:
```python
def run_and_persist_qc_for(
    artifact: Artifact,
    store: ArtifactStore,
    client_id: str,
    engagement_id: str,
    operator_id: str
) -> QCArtifact:
    """
    Run QC rules and persist to ArtifactStore.
    
    1. Determine QC type from artifact type
    2. Run rules engine (ruleset_v1)
    3. Convert results to QCArtifact
    4. Call store.store_qc_artifact()
    5. Return QCArtifact
    """
```

### Phase 2: Operator UI Wiring (MODIFY)

**File**: `operator_v2.py`

**Changes**:

1. **Import QC service** (top of file)
2. **Wire "Run QC" buttons** (4 existing placeholders):
   - Call `run_and_persist_qc_for()`
   - Display QC panel with results
3. **Add QC panels** to approval sections:
   - Show QC status (PASS/WARN/FAIL)
   - Show score and counts
   - List failed checks
4. **Auto-run QC** after draft save/generate:
   - After `store.create_artifact()` or `store.update_artifact()`
   - Call `run_and_persist_qc_for()`
5. **Surface QC errors** in approval flow:
   - Catch `ArtifactValidationError` from QC gate
   - Display with QC panel

### Phase 3: Tests (NEW FILE)

**Create**: `tests/test_qc_enforcement.py`

**Tests**:
1. Approval refused if QC missing
2. Approval refused if QC FAIL
3. Approval refused if QC version mismatch
4. Approval allowed if QC PASS
5. Repeat for Delivery artifact

---

## NO CHANGES NEEDED

**Files that do NOT need modification**:
- ✅ `aicmo/ui/persistence/artifact_store.py` - QC gate already complete
- ✅ `aicmo/ui/quality/qc_models.py` - Models correct
- ✅ `aicmo/ui/quality/rules/` - Rules engine complete
- ✅ `aicmo/ui/gating.py` - Gating logic unchanged

---

## DECISION SUMMARY

### QC Storage Approach: Session State with Version Lock ✅

**Implementation**: Use existing `ArtifactStore.store_qc_artifact()` and `get_qc_for_artifact()`

**Key Format**: `{artifact_id}_v{version}` (already version-locked)

**Storage Location**: `session_state["_qc_artifacts"]`

**Rationale**:
- Infrastructure already exists
- Version locking already implemented
- No ArtifactType enum pollution
- Clean separation of concerns

### QC Generation Trigger Points

**Automatic QC**:
1. After artifact create/update in all tabs
2. Before first approval attempt (if missing)

**Manual QC**:
1. "Run QC" buttons (wire existing placeholders)
2. Revise flow (after amendments saved)

### Legacy deterministic_checks.py

**Decision**: KEEP but MARK DEPRECATED

**Rationale**:
- Used by existing tests
- No immediate harm
- Will naturally phase out as tests migrate to new engine

---

## IMPLEMENTATION PHASES

### Phase 1: QC Service ✅ READY TO IMPLEMENT
- Create `aicmo/ui/quality/qc_service.py`
- Implement `run_and_persist_qc_for()`
- Connect rules engine to ArtifactStore

### Phase 2: Operator Wiring ✅ READY TO IMPLEMENT
- Wire "Run QC" buttons (4 existing)
- Add QC panels to approval sections
- Auto-run QC after draft saves
- Surface QC errors in approval flow

### Phase 3: Tests ✅ READY TO IMPLEMENT
- Create `tests/test_qc_enforcement.py`
- 5+ tests proving enforcement
- No skipped tests

### Phase 4: Documentation ✅ READY TO IMPLEMENT
- Update QC_ENGINE_EVIDENCE.md
- Create QC_WIRING_COMPLETE.md
- Proof commands

### Phase 5: Commit ✅ READY TO IMPLEMENT
- Single commit: "Wire deterministic QC into ArtifactStore approval + operator_v2 UI"
- Push to origin/main

---

## ACCEPTANCE CRITERIA CHECKLIST

- [ ] QC artifacts stored in ArtifactStore with version lock
- [ ] Approvals refuse without QC for same version
- [ ] QC auto-generated after draft save/generate/revise
- [ ] operator_v2 shows QC panels with clear fail reasons
- [ ] "Run QC" buttons functional (4 tabs)
- [ ] Tests prove enforcement (5+ tests, all passing)
- [ ] py_compile passes
- [ ] pytest passes (no skipped tests)
- [ ] Documentation complete
- [ ] Commit created and pushed

---

**Status**: DISCOVERY COMPLETE ✅  
**Next**: Begin Phase 1 - QC Service Implementation
