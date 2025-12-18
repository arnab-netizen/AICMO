# ARTIFACT SYSTEM REFACTOR - QUICK START GUIDE

## What Was Implemented

This refactoring transforms AICMO from a simple lead intake form to a comprehensive **Client Intake system** with artifact-based dependency gating.

### Key Changes

1. **Client Intake Form** - Comprehensive 40+ field form with:
   - Client identity, offer, audience, goals, voice, assets, delivery requirements
   - Polymorphic context (hiring, e-commerce, services)
   - Generation plan (checkbox matrix → job queue)

2. **Artifact System** - Every module produces a versioned artifact:
   - Draft → Revised → Approved lifecycle
   - Approval required to unlock downstream tabs
   - Automatic stale detection when upstream changes

3. **Strict Gating** - Downstream tabs locked until upstream approved:
   - Strategy blocked until Intake approved
   - Creatives blocked until Strategy approved
   - Etc.

4. **Self-Test** - System tab has automated test suite to verify wiring

## How to Use

### 1. Start the Dashboard

```bash
cd /workspaces/AICMO
streamlit run operator_v2.py --server.port 8502
```

### 2. Fill Client Intake

Navigate to "Intake" tab (renamed from "Lead Intake"):

**Minimum Required Fields:**
- Client Name: "Test Corp"
- Website: "https://test.com"
- Industry: "Technology"
- Geography: "USA"
- Primary Offer: "SaaS Platform"
- Objective: "Leads"
- Target Audience: "B2B Companies"
- Pain Points: "Manual processes"
- Desired Outcomes: "Automation"
- Tone/Voice: "Professional but friendly"

**Optional:**
- Select generation plan checkboxes for what you want AICMO to generate

Click **"🚀 Generate"**

### 3. Verify Gating

Try to navigate to "Strategy" tab:
- Generate button should be **DISABLED**
- Warning: "Blocked: missing intake (draft - must be approved)"

### 4. Approve Intake

Return to "Intake" tab, scroll to approval section:
1. Review the generated output in "Output Preview"
2. (Optional) Edit in "Amend Deliverable" section
3. Click **"👍 Approve Deliverable"**
4. Toast notification: "✅ Client Intake approved! Strategy tab unlocked."

### 5. Verify Unlock

Navigate to "Strategy" tab:
- Generate button should now be **ENABLED**
- Can proceed with strategy generation

### 6. Run Self-Test

Navigate to "System" tab:
1. Click **"▶️ Run UI Wiring Self-Test"**
2. Wait 2-3 seconds
3. Should see 8 tests all showing **✅ PASS**

## Test Results to Expect

```
✅ PASS | Create intake artifact | ID: abc123...
✅ PASS | Strategy gating (intake draft) | Blocked: intake (draft - must be approved)
✅ PASS | Approve intake artifact | Status: approved
✅ PASS | Strategy gating (intake approved) | Strategy unlocked
✅ PASS | Create strategy artifact | ID: def456...
✅ PASS | Creatives gating (strategy draft) | Blocked: strategy (draft - must be approved)
✅ PASS | Creatives gating (strategy approved) | Creatives unlocked
✅ PASS | Stale cascade | Flagged 1 artifacts

🎉 All tests passed! (8 passed, 0 warnings)
```

## Files You Can Inspect

### Core Implementation
- `/workspaces/AICMO/operator_v2.py` - Main dashboard (2,980 lines)
  - Lines 1-50: Build stamp
  - Lines 200-400: Comprehensive Client Intake form
  - Lines 1563-1750: Intake artifact creation
  - Lines 1040-1070: Approval workflow
  - Lines 2721-2900: Self-test suite

### New Modules
- `/workspaces/AICMO/aicmo/ui/persistence/artifact_store.py` (589 lines)
  - Artifact data models
  - ArtifactStore CRUD
  - Gating logic
  - Validation

- `/workspaces/AICMO/aicmo/ui/generation_plan.py` (390 lines)
  - Job DAG system
  - Generation plan builder

### Documentation
- `/workspaces/AICMO/ARTIFACT_SYSTEM_IMPLEMENTATION_COMPLETE.md` (comprehensive)

## Verification Commands

```bash
# 1. Check syntax
python -m py_compile operator_v2.py

# 2. Check imports
python -c "import operator_v2; print('✅ operator_v2 import OK')"
python -c "from aicmo.ui.persistence.artifact_store import ArtifactStore; print('✅ artifact_store import OK')"
python -c "from aicmo.ui.generation_plan import GenerationPlan; print('✅ generation_plan import OK')"

# 3. Start dashboard
streamlit run operator_v2.py --server.port 8502
```

## Known Limitations (Deferred for Future)

1. **Strategy/Creatives/Execution Tabs** - Still use old workflow, not yet artifact-integrated
2. **Autonomy Job Runner** - Generation plan exists but runner not implemented
3. **LLM Validation** - Framework present but not wired
4. **Stale Cascade UI** - Works but no visual indicators yet

## What Works NOW

✅ Client Intake form with 40+ fields  
✅ Artifact creation with version tracking  
✅ Approval workflow  
✅ Gating enforcement (Strategy blocked until Intake approved)  
✅ Stale cascade detection  
✅ Self-test suite (8 automated tests)  
✅ Build stamp visible in header  

## Next Steps (Future Sessions)

1. Integrate Strategy/Creatives/Execution tabs with artifact system
2. Implement Autonomy job runner (DAG execution)
3. Add Playwright E2E test for Intake → Strategy gating
4. Wire LLM validation (optional)
5. Add stale cascade visual indicators

## Questions?

See `/workspaces/AICMO/ARTIFACT_SYSTEM_IMPLEMENTATION_COMPLETE.md` for full documentation.
