# AICMO Consistency Correction Plan

**Date:** December 17, 2025  
**Scope:** Full system consistency pass (STOP FEATURE ADDITION)  
**Goal:** Fix internal inconsistencies, enforce strict workflow, prove correctness

---

## 🚨 CRITICAL ISSUES IDENTIFIED

1. **Strategy Contract Mismatch** - Current Strategy ≠ Required 8-Layer Contract
2. **Inconsistent Active Context** - Multiple session key patterns
3. **Weak Gating** - Approval requirements not strictly enforced
4. **Generic Downstream Tabs** - Not hydrating from correct upstream layers
5. **Missing Runtime Proof** - No evidence panel to prove correctness

---

## ✅ PHASE 1: Entrypoint & Store Truth

### Status: ✅ MOSTLY COMPLETE (verify & enhance)

**1.1 Single UI Entrypoint**
- ✅ `operator_v2.py` is the single dashboard
- ⏳ Add footer banner with source file on every page
- ⏳ Verify no other dashboard files in execution path

**1.2 Single ArtifactStore Instance**
- ✅ Factory exists: `get_artifact_store()` (lines 260-290)
- ✅ Cached in session: `_canonical_artifact_store`
- ✅ Has alias: `get_store = get_artifact_store`
- ⏳ Verify ALL tabs use `get_store()` (no direct instantiation)

**1.3 Runtime Proof**
- ⏳ Create System Evidence Panel showing:
  - `operator_v2.__file__`
  - `artifact_store.__file__`
  - `id(get_store())`
  - Persistence mode
  - Last write/read timestamps

**Action Items:**
- [ ] Add footer banner to all tabs
- [ ] Audit all tabs for direct `ArtifactStore()` calls
- [ ] Build System Evidence Panel (Phase 7)

---

## ⏳ PHASE 2: Active Context Contract

### Status: PARTIAL (needs enforcement)

**2.1 Canonical Session Keys**
Required ONLY keys:
- `active_campaign_id`
- `active_client_id`  
- `active_engagement_id`

**Current State:** (Need to audit)
- ⏳ Check for aliases/alternatives
- ⏳ Enforce NO fallbacks

**2.2 Active Context Header**
- ✅ Function exists: `render_active_context_header()` (line 295+)
- ⏳ Verify it shows:
  - Campaign name
  - Client name
  - Engagement ID
  - Current stage
  - Buttons: Change Campaign / Clear Context
- ⏳ Audit ALL tabs call this header

**Action Items:**
- [ ] Audit session keys, remove aliases
- [ ] Verify active context header on all tabs
- [ ] Add "Change Campaign" / "Clear Context" buttons

---

## 🚨 PHASE 3: Strategy Contract (CRITICAL FIX)

### Status: ❌ WRONG IMPLEMENTATION

**THE PROBLEM:**
Current Strategy schema does NOT match user's 8-layer specification.

**THE FIX:**
Replace entire Strategy tab with 8-Layer Contract:

### Layer 1: Business Reality Alignment
- business_model_summary
- revenue_streams
- unit_economics (CAC/LTV or unknown)
- pricing_logic
- growth_constraint
- bottleneck (Demand/Awareness/Trust/Conversion/Retention)
- risk_tolerance
- regulatory_constraints

### Layer 2: Market & Competitive Truth
- category_maturity
- competitive_vectors (price/speed/trust/brand/distribution)
- white_space_logic
- what_not_to_do

### Layer 3: Audience Decision Psychology
- awareness_state
- pain_intensity
- objection_hierarchy
- trust_transfer_mechanism

### Layer 4: Value Proposition Architecture
- core_promise (single sentence)
- proof_stack (social/authority/mechanism)
- sacrifice_framing
- differentiation_logic

### Layer 5: Strategic Narrative
- narrative_spine (problem→tension→resolution)
- enemy_definition
- repetition_logic

### Layer 6: Channel Strategy
For EACH channel:
- strategic_role (discovery/trust/conversion/retention)
- allowed_content_types
- kpi
- kill_criteria

### Layer 7: Execution Constraints
- tone_boundaries
- forbidden_language
- claim_boundaries
- visual_constraints
- compliance_rules

### Layer 8: Measurement & Learning Loop
- success_definition
- leading_indicators
- lagging_indicators
- review_cadence
- decision_rules (If X → do Y)

**Action Items:**
- [ ] DELETE current Strategy UI (render_strategy_tab)
- [ ] Implement new 8-layer Strategy editor
- [ ] Update validation: `validate_strategy_contract()` to check all 8 layers
- [ ] Update artifact_store.py Strategy validation

---

## ⏳ PHASE 4: Downstream Hydration

### Status: PARTIAL (needs layer-specific hydration)

**4.1 Creatives MUST Hydrate From:**
- L3: decision psychology → inform angles
- L4: value architecture → core message
- L5: narrative → story structure
- L6: channel roles → platform selection
- L7: constraints → tone/claims

**4.2 Execution MUST Hydrate From:**
- L6: channel strategy → posting schedule
- L7: constraints → governance

**4.3 Monitoring MUST Hydrate From:**
- L8: KPIs, cadence, decision rules

**4.4 Delivery MUST Include:**
- Intake summary
- Full 8-layer Strategy
- Creatives
- Execution
- Monitoring

**Action Items:**
- [ ] Update Creatives tab to read Strategy L3-L7
- [ ] Update Execution tab to read Strategy L6-L7
- [ ] Update Monitoring tab to read Strategy L8
- [ ] Update Delivery tab to package all artifacts

---

## ⏳ PHASE 5: Gating & Approval Correction

### Final Gating Map (LOCK THIS):

| Tab | Requires APPROVED |
|-----|-------------------|
| Strategy | Intake |
| Creatives | Strategy |
| Execution | Creatives |
| Monitoring | Execution |
| Delivery | Intake + Strategy + Creatives + Execution |

**Rules:**
- ✅ Monitoring approval does NOT unlock Delivery by itself
- ✅ Delivery requires ALL 4 core artifacts APPROVED
- ⏳ Verify gating is STRICT (no bypasses)

**Action Items:**
- [ ] Audit gating checks in all tabs
- [ ] Verify artifact_store.GATING_MAP matches
- [ ] Ensure NO auto-approval anywhere

---

## ⏳ PHASE 6: Delivery Tab Correction

### Status: NEEDS UPDATE

**Current Issue:** Delivery may be acting as generator

**Fix:** Delivery is PACKAGER only

**Must Include:**
- ✅ Artifact selection (checkboxes)
- ✅ Export formats (PDF/PPTX/JSON/ZIP)
- ✅ Delivery method
- ⏳ Pre-flight checklist:
  - Approvals present
  - QC passed
  - Compliance respected
  - Branding applied
  - Placeholders removed

**Action Items:**
- [ ] Review Delivery tab implementation
- [ ] Add missing pre-flight checks
- [ ] Ensure gating map is correct

---

## ⏳ PHASE 7: System Evidence Panel (MANDATORY)

### Status: MISSING

**Create System "Evidence Panel" Tab:**

**Section 1: Runtime Truth**
```
Dashboard File: /workspaces/AICMO/operator_v2.py
Store File: /workspaces/AICMO/aicmo/ui/persistence/artifact_store.py
Store ID: 140234567890123
Persistence Mode: inmemory
```

**Section 2: Active Context**
```
Campaign ID: camp_abc123
Client ID: client_xyz789
Engagement ID: eng_456def
Current Stage: Strategy
```

**Section 3: Artifact Table**
| Artifact | Status | Version | Approved At | Approved By |
|----------|--------|---------|-------------|-------------|
| Intake | APPROVED | v1 | 2025-12-17 | operator |
| Strategy | DRAFT | v1 | - | - |
| Creatives | - | - | - | - |
| Execution | - | - | - | - |
| Monitoring | - | - | - | - |
| Delivery | - | - | - | - |

**Section 4: Flow Checklist**
```
✓ Campaign selected
✓ Intake approved
✗ Strategy approved
✗ Creatives approved
✗ Execution approved
✗ Delivery unlocked
```

**Section 5: Evidence Queries**
- Session state dump
- Artifact content preview
- Lineage graph

**Action Items:**
- [ ] Create `render_system_evidence_tab()`
- [ ] Add to tab navigation
- [ ] Implement all 5 sections

---

## ⏳ PHASE 8: Tests (Proof, Not Claims)

### Status: PARTIAL

**8.1 Unit Tests (pytest)**
```python
# tests/test_consistency.py
def test_campaign_creation_and_selection():
    """Campaign must exist before Intake"""
    pass

def test_intake_requires_campaign():
    """Intake cannot save without campaign"""
    pass

def test_intake_approval_unlocks_strategy():
    """Strategy gates on Intake APPROVED"""
    pass

def test_strategy_requires_8_layers():
    """Strategy approval requires all 8 layers"""
    pass

def test_creatives_gates_on_strategy():
    """Creatives gates on Strategy APPROVED"""
    pass

def test_execution_gates_on_creatives():
    """Execution gates on Creatives APPROVED"""
    pass

def test_monitoring_gates_on_execution():
    """Monitoring gates on Execution APPROVED"""
    pass

def test_delivery_gates_on_all_core():
    """Delivery gates on Intake+Strategy+Creatives+Execution APPROVED"""
    pass

def test_store_consistency():
    """Store instance is singleton"""
    pass
```

**8.2 E2E Tests (Playwright)**
```python
# tests/e2e/test_full_workflow.py
def test_complete_workflow():
    """Full workflow: Campaign → Intake → Strategy → ... → Delivery"""
    pass

def test_approval_unlocks():
    """Verify approvals unlock next stage"""
    pass

def test_delivery_blocked_until_approvals():
    """Delivery blocked until all core approved"""
    pass
```

**Action Items:**
- [ ] Write unit tests
- [ ] Write E2E tests
- [ ] Ensure all tests pass

---

## 🛑 STOP CONDITIONS

**DO NOT STOP UNTIL:**
- [ ] Strategy schema matches 8 layers above
- [ ] Downstream tabs hydrate correctly from upstream layers
- [ ] System Evidence Panel proves runtime truth
- [ ] All gating is strict and correct
- [ ] Tests pass
- [ ] No generic UI remnants remain

---

## EXECUTION ORDER

1. **Phase 1** → Verify store factory, add footer (quick wins)
2. **Phase 2** → Fix active context, enforce header everywhere
3. **Phase 3** → **CRITICAL** - Replace Strategy with 8-layer contract
4. **Phase 4** → Fix downstream hydration (depends on Phase 3)
5. **Phase 5** → Audit and fix gating
6. **Phase 6** → Fix Delivery tab
7. **Phase 7** → Build System Evidence Panel
8. **Phase 8** → Write tests

---

## FILES TO MODIFY

### Primary Files:
- [ ] `operator_v2.py` - All tab renderers
- [ ] `aicmo/ui/persistence/artifact_store.py` - Validation functions
- [ ] `tests/test_consistency.py` - New test file
- [ ] `tests/e2e/test_full_workflow.py` - New E2E tests

### Estimated Changes:
- Strategy tab: **COMPLETE REWRITE** (~500-800 lines)
- Creatives tab: **MAJOR UPDATE** (hydration logic)
- Execution tab: **MODERATE UPDATE** (hydration from L6-L7)
- Monitoring tab: **MODERATE UPDATE** (hydration from L8)
- Delivery tab: **MINOR UPDATE** (pre-flight checklist)
- System Evidence tab: **NEW** (~200-300 lines)
- Tests: **NEW** (~300-500 lines)

---

**Total Estimated LOC:** ~1,500-2,500 lines of changes/additions
**Estimated Time:** 6-10 hours of careful, systematic work
**Risk Level:** HIGH (requires careful testing at each phase)

---

## COMMIT STRATEGY

After each phase:
```bash
git add <modified_files>
git commit -m "fix(phase-X): <description>"
```

Final commit:
```bash
git commit -m "fix(consistency): Complete system consistency correction

BREAKING CHANGE: Full workflow correction pass

- Replace Strategy with 8-layer contract (Phases 1-3)
- Fix downstream hydration from correct layers (Phase 4)
- Enforce strict gating and approvals (Phase 5)
- Correct Delivery tab as packager (Phase 6)
- Add System Evidence Panel (Phase 7)
- Add comprehensive tests (Phase 8)

All stop conditions met, system proven consistent."
```
