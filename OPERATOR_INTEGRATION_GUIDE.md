# Operator Integration Guide - Exact Changes Required

**Target File**: `/workspaces/AICMO/operator_v2.py`  
**Status**: Implementation ready (9 runners need HTTP client integration)  
**Scope**: 9 runner functions (lines 902-1279)

---

## 1. Add Imports (Top of File)

**Location**: After existing imports section, around line 1-50

```python
# Add these imports for backend communication
from streamlit_backend_client import (
    get_backend_url,
    backend_post_json,
    validate_response,
)
from backend.schemas_deliverables import (
    create_success_envelope,
    create_failed_envelope,
    DeliverablesEnvelope,
)
```

---

## 2. Add Helper Function

**Location**: After runner functions, around line 1280

```python
def _convert_deliverables_to_markdown(deliverables: list) -> str:
    """Convert deliverables list to editable markdown"""
    if not deliverables:
        return "# Draft Content\n\n(No deliverables generated)"
    
    markdown = "# Generated Content\n\n"
    for i, d in enumerate(deliverables, 1):
        title = d.get("title", f"Deliverable {i}")
        content = d.get("content_markdown", "")
        
        markdown += f"## {i}. {title}\n\n"
        if content:
            markdown += f"{content}\n\n"
    
    markdown += "\n---\n\n## Operator Notes\n\nAdd any amendments here:\n"
    return markdown
```

---

## 3. Update Runner Functions

### Pattern for All 9 Runners:

```python
def run_RUNNER_NAME_step(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Run DESCRIPTION via backend"""
    
    # ✅ STEP 1: Validate inputs
    try:
        required_field = inputs.get("required_field", "").strip()
        if not required_field:
            return create_failed_envelope(
                module="runner_name",
                run_id=str(uuid.uuid4()),
                error_type="VALIDATION_ERROR",
                error_message="required_field is required",
            ).to_dict()
    except Exception as e:
        return create_failed_envelope(
            module="runner_name",
            run_id=str(uuid.uuid4()),
            error_type="INPUT_ERROR",
            error_message=str(e),
        ).to_dict()
    
    # ✅ STEP 2: Check backend URL
    backend_url = get_backend_url()
    if not backend_url:
        return {
            "status": "FAILED",
            "error": "BACKEND_URL or AICMO_BACKEND_URL not configured",
            "trace_id": None,
        }
    
    # ✅ STEP 3: Call backend
    try:
        response = backend_post_json(
            path="/api/v1/runner_name/generate",
            payload={
                "required_field": required_field,
                "other_field": inputs.get("other_field"),
            },
        )
    except Exception as e:
        log.error(f"Backend call failed: {e}")
        return create_failed_envelope(
            module="runner_name",
            run_id=str(uuid.uuid4()),
            error_type="BACKEND_ERROR",
            error_message=f"Backend connection failed: {str(e)}",
        ).to_dict()
    
    # ✅ STEP 4: Validate response envelope
    is_valid, error_msg = validate_response(response)
    if not is_valid:
        return {
            "status": "FAILED",
            "error": f"Contract validation failed: {error_msg}",
            "trace_id": response.trace_id,
            "deliverables": [],
        }
    
    # ✅ STEP 5: Convert to draft markdown
    draft_markdown = _convert_deliverables_to_markdown(response.deliverables)
    
    # ✅ STEP 6: Store in session state
    tab_key = "runner_name"
    st.session_state[f"{tab_key}__draft_text"] = draft_markdown
    st.session_state[f"{tab_key}__run_id"] = response.run_id
    st.session_state[f"{tab_key}__trace_id"] = response.trace_id
    
    # ✅ STEP 7: Return success
    return {
        "status": response.status,
        "deliverables": response.deliverables,
        "meta": response.meta,
        "trace_id": response.trace_id,
        "draft_text": draft_markdown,
    }
```

---

## 4. Specific Runner Updates

### Runner 1: run_intake_step (Line 902)

**Backend Endpoint**: `POST /api/v1/intake/generate`

**Changes**:
```python
def run_intake_step(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Run intake workflow via backend"""
    try:
        name = inputs.get("name", "").strip()
        email = inputs.get("email", "").strip()
        company = inputs.get("company", "").strip()
        
        if not (name and email):
            return create_failed_envelope(
                module="intake",
                run_id=str(uuid.uuid4()),
                error_type="VALIDATION_ERROR",
                error_message="Name and email are required",
            ).to_dict()
        
        backend_url = get_backend_url()
        if not backend_url:
            return {"status": "FAILED", "error": "Backend not configured"}
        
        response = backend_post_json(
            path="/api/v1/intake/generate",
            payload={
                "name": name,
                "email": email,
                "company": company,
            },
        )
        
        is_valid, error = validate_response(response)
        if not is_valid:
            return {"status": "FAILED", "error": error, "trace_id": response.trace_id}
        
        # Store draft
        draft_text = _convert_deliverables_to_markdown(response.deliverables)
        st.session_state["intake__draft_text"] = draft_text
        st.session_state["intake__run_id"] = response.run_id
        
        return {
            "status": response.status,
            "deliverables": response.deliverables,
            "meta": response.meta,
            "trace_id": response.trace_id,
        }
    
    except Exception as e:
        log.error(f"Intake error: {e}")
        return create_failed_envelope(
            module="intake",
            run_id=str(uuid.uuid4()),
            error_type="INTERNAL_ERROR",
            error_message=str(e),
        ).to_dict()
```

---

### Runner 2: run_strategy_step (Line 930)

**Backend Endpoint**: `POST /api/v1/strategy/generate`

**Changes**:
```python
def run_strategy_step(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Run strategy generation via backend"""
    try:
        campaign_name = inputs.get("campaign_name", "").strip()
        if not campaign_name:
            return create_failed_envelope(
                module="strategy",
                run_id=str(uuid.uuid4()),
                error_type="VALIDATION_ERROR",
                error_message="Campaign name is required",
            ).to_dict()
        
        backend_url = get_backend_url()
        if not backend_url:
            return {"status": "FAILED", "error": "Backend not configured"}
        
        response = backend_post_json(
            path="/api/v1/strategy/generate",
            payload={
                "campaign_name": campaign_name,
                "objectives": inputs.get("objectives", []),
                "platforms": inputs.get("platforms", []),
                "budget": inputs.get("budget", 0),
            },
        )
        
        is_valid, error = validate_response(response)
        if not is_valid:
            return {"status": "FAILED", "error": error, "trace_id": response.trace_id}
        
        draft_text = _convert_deliverables_to_markdown(response.deliverables)
        st.session_state["strategy__draft_text"] = draft_text
        st.session_state["strategy__run_id"] = response.run_id
        
        return {
            "status": response.status,
            "deliverables": response.deliverables,
            "meta": response.meta,
            "trace_id": response.trace_id,
        }
    
    except Exception as e:
        log.error(f"Strategy error: {e}")
        return create_failed_envelope(
            module="strategy",
            run_id=str(uuid.uuid4()),
            error_type="INTERNAL_ERROR",
            error_message=str(e),
        ).to_dict()
```

---

### Runner 3-9: Pattern (Same approach for all)

Apply the same pattern to:
- **run_creatives_step** (line 966) → `/api/v1/creatives/generate`
- **run_execution_step** (line 1032) → `/api/v1/execution/generate`
- **run_monitoring_step** (line 1062) → `/api/v1/monitoring/generate`
- **run_leadgen_step** (line 1093) → `/api/v1/leadgen/generate`
- **run_autonomy_step** (line 1203) → `/api/v1/autonomy/generate`
- **run_delivery_step** (line 1223) → `/api/v1/delivery/generate`
- **run_learn_step** (line 1252) → `/api/v1/learn/generate`

---

## 5. Update render_* Functions for Draft-Amend-Approve-Export

For each tab renderer (e.g., `render_intake_tab`, `render_strategy_tab`, etc.), add sections after Generate:

```python
def render_RUNNER_NAME_tab():
    """Render RUNNER_NAME tab with draft-amend-approve-export flow"""
    
    # ... existing input collection code ...
    
    # Generate button (existing)
    if st.button("Generate", key=f"gen_button_{tab_key}"):
        result = run_RUNNER_NAME_step(inputs)
        st.session_state[f"{tab_key}__last_result"] = result
    
    # ===== NEW: Draft-Amend-Approve-Export Section =====
    
    if st.session_state.get(f"{tab_key}__last_result", {}).get("status") == "SUCCESS":
        st.divider()
        st.subheader("📝 Draft - Amend - Approve - Export")
        
        # A) Output Preview
        with st.expander("📖 Output Preview", expanded=True):
            draft_text = st.session_state.get(f"{tab_key}__draft_text", "")
            st.markdown(draft_text)
        
        # B) Amend Section
        col1, col2 = st.columns([3, 1])
        with col1:
            amended_text = st.text_area(
                "Edit Draft Content",
                value=st.session_state.get(f"{tab_key}__draft_text", ""),
                height=300,
                key=f"amend_area_{tab_key}",
            )
        with col2:
            if st.button("💾 Save Amendments", key=f"save_amend_{tab_key}"):
                st.session_state[f"{tab_key}__draft_text"] = amended_text
                st.session_state[f"{tab_key}__draft_saved_at"] = datetime.now().isoformat()
                st.success("✅ Amendments saved")
            
            if st.button("↩️ Reset", key=f"reset_draft_{tab_key}"):
                result = st.session_state.get(f"{tab_key}__last_result", {})
                deliverables = result.get("deliverables", [])
                draft_text = _convert_deliverables_to_markdown(deliverables)
                st.session_state[f"{tab_key}__draft_text"] = draft_text
                st.info("Draft reset to generated version")
        
        # C) Approve Section
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve This Draft", key=f"approve_{tab_key}"):
                st.session_state[f"{tab_key}__approved_text"] = st.session_state.get(f"{tab_key}__draft_text", "")
                st.session_state[f"{tab_key}__approved_at"] = datetime.now().isoformat()
                st.session_state[f"{tab_key}__approved_by"] = "operator"
                st.session_state[f"{tab_key}__export_ready"] = True
                st.success("✅ Draft approved for export")
        
        with col2:
            if st.session_state.get(f"{tab_key}__export_ready"):
                if st.button("❌ Revoke Approval", key=f"revoke_{tab_key}"):
                    st.session_state[f"{tab_key}__export_ready"] = False
                    st.info("Approval revoked")
        
        # D) Export Section
        st.markdown("---")
        if st.session_state.get(f"{tab_key}__export_ready"):
            st.success("✅ Ready for export")
            
            col1, col2 = st.columns(2)
            with col1:
                approved_text = st.session_state.get(f"{tab_key}__approved_text", "")
                filename = f"aicmo_{tab_key}_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
                st.download_button(
                    label="📥 Download Markdown",
                    data=approved_text,
                    file_name=filename,
                    mime="text/markdown",
                    key=f"download_md_{tab_key}",
                )
            
            with col2:
                result = st.session_state.get(f"{tab_key}__last_result", {})
                json_data = json.dumps(result, indent=2, default=str)
                filename_json = f"aicmo_{tab_key}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=filename_json,
                    mime="application/json",
                    key=f"download_json_{tab_key}",
                )
        else:
            st.warning("⚠️ Approve the draft before exporting")
        
        # E) Debug expander
        with st.expander("🔧 Debug Details"):
            st.json(st.session_state.get(f"{tab_key}__last_result", {}))
```

---

## 6. Verification Steps After Updates

### Step 1: Syntax Check
```bash
cd /workspaces/AICMO
python -m py_compile operator_v2.py
```
**Expected**: No output = success ✅

### Step 2: Find Remaining Stubs
```bash
grep -n "In production\|Stub:\|mock\|return {\"topic\"\|return {\"status\"" operator_v2.py | head -50
```
**Expected**: Most should be gone, only AICMO_DEV_STUBS=1 branches remain

### Step 3: Check Imports
```bash
head -100 operator_v2.py | grep "from streamlit_backend_client\|from backend.schemas"
```
**Expected**: Both import lines visible ✅

### Step 4: Run Smoke Test
```bash
python tools/smoke_generate.py
```
**Expected**: Exit code 0, all tests pass ✅

### Step 5: Manual UI Test
```bash
# Terminal 1: Start backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start Streamlit
streamlit run operator_v2.py
```

**Expected Flow**:
1. Open browser to http://localhost:8501
2. Select any tab (e.g., "Campaigns")
3. Fill in inputs
4. Click "Generate"
5. See deliverables in "Output Preview"
6. Edit in "Edit Draft Content"
7. Click "Save Amendments"
8. Click "Approve This Draft"
9. Click "Download Markdown"
10. File downloads successfully ✅

---

## 7. Required Backend Endpoints

For each runner, backend must have:

| Runner | Endpoint | Expected Response |
|--------|----------|-------------------|
| intake | POST /api/v1/intake/generate | DeliverablesEnvelope with lead confirmation |
| strategy | POST /api/v1/strategy/generate | DeliverablesEnvelope with strategy deliverables |
| creatives | POST /api/v1/creatives/generate | DeliverablesEnvelope with creative content |
| execution | POST /api/v1/execution/generate | DeliverablesEnvelope with execution plan |
| monitoring | POST /api/v1/monitoring/generate | DeliverablesEnvelope with monitoring metrics |
| leadgen | POST /api/v1/leadgen/generate | DeliverablesEnvelope with leads |
| autonomy | POST /api/v1/autonomy/generate | DeliverablesEnvelope with autonomous actions |
| delivery | POST /api/v1/delivery/generate | DeliverablesEnvelope with delivery status |
| learn | POST /api/v1/learn/generate | DeliverablesEnvelope with learning insights |

**Each must return**:
```json
{
  "status": "SUCCESS",
  "run_id": "uuid",
  "module": "runner_name",
  "meta": { "timestamp": "...", "provider": "openai", "model": "..." },
  "deliverables": [{ "id": "...", "title": "...", "content_markdown": "..." }],
  "error": null
}
```

---

## 8. Import Statements Needed

Add these at top of operator_v2.py:

```python
import uuid
import json
import logging
from datetime import datetime
from streamlit_backend_client import (
    get_backend_url,
    backend_post_json,
    validate_response,
)
from backend.schemas_deliverables import (
    create_success_envelope,
    create_failed_envelope,
)

log = logging.getLogger(__name__)
```

---

## Summary of Changes

**Total Modifications**:
- ✅ Add 3-5 import lines
- ✅ Add 1 helper function (_convert_deliverables_to_markdown)
- ✅ Update 9 runner functions (replace stubs with HTTP calls)
- ✅ Update 9+ render_*_tab functions (add draft-amend-approve-export section)

**Lines of Code Changed**: ~300-400 lines

**Time to Complete**: 2-3 hours

**Verification Commands**: 5 total (syntax, grep, imports, smoke test, manual UI)

---

**Status**: Ready to implement  
**Next Action**: Apply these changes systematically to operator_v2.py
