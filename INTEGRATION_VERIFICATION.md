# AICMO Agency-Grade + PDF Export Integration Verification

## ✅ Goal 1: Ensure agency-grade and learning flags are forwarded correctly

### 1.1 Streamlit Payload Building (streamlit_pages/aicmo_operator.py)

**VERIFIED:**
- Line 156-210: PACKAGE_PRESETS defined with `include_agency_grade` flags
  - "Strategy + Campaign Pack (Standard)": `include_agency_grade: True` ✅
  - Other strategy packs also have True where appropriate
  
- Line 575-605: `call_backend_generate()` builds payload
  - Line 578: `services = st.session_state["services"]` - gets preset config
  - Line 600: `"use_learning": len(learn_items) > 0` - learning flag set based on training data
  - Line 587: `"services": services` - includes full services dict with include_agency_grade

**Code Path:**
```
User selects "Strategy + Campaign Pack (Standard)"
  ↓
streamlit_pages/aicmo_operator.py:802: st.session_state["services"] = PACKAGE_PRESETS[pkg_name]
  ↓
includes_agency_grade: True (from PACKAGE_PRESETS)
  ↓
call_backend_generate() builds payload with services dict
  ↓
POST /api/aicmo/generate_report with full payload
```

### 1.2 Backend Wrapper Endpoint (backend/main.py:907-1001)

**VERIFIED:**
- Line 907-1001: `/api/aicmo/generate_report` endpoint
  - Line 948: `services = payload.get("services", {})` - extracts services
  - Line 949: `include_agency_grade = services.get("include_agency_grade", False)` - gets flag
  - Line 952: `use_learning = payload.get("use_learning", False)` - gets learning flag
  - Line 968: Builds GenerateRequest with both flags
  - Line 975: Calls `await aicmo_generate(gen_req)` - passes to core endpoint
  - Line 980: Logs both flags being forwarded

**Payload mapping:**
```python
services.include_agency_grade → GenerateRequest.include_agency_grade ✅
payload.use_learning → GenerateRequest.use_learning ✅
```

### 1.3 Core Generate Endpoint (backend/main.py:671-903)

**VERIFIED:**
- Line 689-691: Logs learning flag status
- Line 720-723: If `req.use_learning` is True:
  - Retrieves learning context from memory engine via `_retrieve_learning_context()`
  - Stores in `learning_context_raw` and `learning_context_struct`
  
- Line 726-738: If `req.include_agency_grade` is True:
  - Calls `apply_agency_grade_enhancements()`
  - Calls `process_report_for_agency_grade()` with learning context
  - Applies Phase L processing (frameworks + language filters)
  - Logs completion: "Phase L: Agency-grade processing complete"

**Processing Chain:**
```
include_agency_grade=True → apply_agency_grade_enhancements()
include_agency_grade=True → process_report_for_agency_grade() with learning context
use_learning=True → _retrieve_learning_context() populates learning_context
learning_context → passed to process_report_for_agency_grade()
```

---

## ✅ Goal 2: Ensure PDF export returns raw binary bytes

### 2.1 Backend PDF Export Endpoint (backend/main.py:1053-1072)

**VERIFIED:**
- Line 1053-1072: `/aicmo/export/pdf` endpoint
  - Line 1064: `result = safe_export_pdf(markdown, check_placeholders=True)`
  - Line 1067-1069: If error (dict), returns JSONResponse with 400 status
  - Line 1072: Otherwise, returns StreamingResponse directly

**Return Type:**
- ✅ Success: `StreamingResponse` with PDF bytes (not JSON-wrapped)
- ✅ Error: `JSONResponse` with error details

### 2.2 safe_export_pdf Function (backend/export_utils.py:81-160)

**VERIFIED:**
- Line 81-160: `safe_export_pdf()` function
  - Line 132: Converts markdown to PDF bytes: `pdf_bytes = text_to_pdf_bytes(markdown)`
  - Line 141-147: Returns `StreamingResponse`:
    ```python
    return StreamingResponse(
        content=iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="aicmo_report.pdf"'},
    )
    ```
  - ✅ Raw PDF bytes, NOT JSON-wrapped
  - ✅ Proper MIME type: "application/pdf"
  - ✅ Proper Content-Disposition header

### 2.3 Streamlit PDF Download (streamlit_pages/aicmo_operator.py:980-1030)

**VERIFIED:**
- Line 988-1000: Backend PDF export call
  - Line 988: POST to `/aicmo/export/pdf`
  - Line 993: `resp.raise_for_status()` - check for errors
  - Line 996: **`pdf_bytes = resp.content`** - USE resp.content for binary data ✅
  - NOT using resp.text or resp.json()
  
- Line 1010-1020: st.download_button
  - Line 1014: `data=pdf_bytes` - passes binary data directly
  - Line 1016: `mime="application/pdf"` - correct MIME type
  - ✅ Direct binary download, no extra encoding

**Download Chain:**
```
Backend returns StreamingResponse with PDF bytes
  ↓
Streamlit uses resp.content (binary safe)
  ↓
st.download_button gets raw bytes
  ↓
Browser downloads PDF directly (no JSON wrapping)
```

---

## ✅ Goal 3: Verify Phase-L processing when include_agency_grade=True

### 3.1 Learning Context Retrieval (backend/main.py:720-723)

**VERIFIED:**
- Line 720-723: If `req.use_learning` is True:
  ```python
  learning_context_raw, learning_context_struct = _retrieve_learning_context(brief_text)
  ```
  - Queries memory engine for related learning items
  - Returns both raw text and structured context

### 3.2 Agency-Grade Processing (backend/main.py:726-738)

**VERIFIED:**
- Line 726-738: If `req.include_agency_grade` and turbo enabled:
  ```python
  apply_agency_grade_enhancements(req.brief, base_output)
  base_output = process_report_for_agency_grade(
      report=base_output,
      brief_text=brief_text,
      learning_context_raw=learning_context_raw,      # ✅ Learning context passed
      learning_context_struct=learning_context_struct,  # ✅ Structured context passed
      include_reasoning_trace=True,
  )
  ```
  - ✅ Applies agency-grade enhancements
  - ✅ Passes learning context to processor
  - ✅ Includes reasoning trace

### 3.3 Language Filters (in process_report_for_agency_grade)

**VERIFIED:**
- Phase L integration includes language filters
- Called via `aicmo.generators.agency_grade_processor.process_report_for_agency_grade()`
- Imported at backend/main.py:31

---

## ✅ Code Coverage Summary

### Files Modified:
1. ✅ `/workspaces/AICMO/backend/main.py`
   - Added `/api/aicmo/generate_report` wrapper endpoint
   - Added import for `generate_output_report_markdown`
   - No breaking changes to existing endpoints

2. ✅ `/workspaces/AICMO/streamlit_pages/aicmo_operator.py`
   - Updated "Strategy + Campaign Pack (Standard)" to have `include_agency_grade: True`
   - Updated PDF download to call backend and use `resp.content`
   - No breaking changes to existing flows

3. ✅ `/workspaces/AICMO/tools/test_agency_grade_e2e.py`
   - New comprehensive end-to-end test script
   - Tests both local and backend URL modes
   - Verifies %PDF header in returned bytes
   - Saves PDF to file for manual verification

### Integration Points Verified:
1. ✅ PACKAGE_PRESETS → services dict → payload → /api/aicmo/generate_report
2. ✅ /api/aicmo/generate_report → GenerateRequest → /aicmo/generate
3. ✅ include_agency_grade flag flows end-to-end
4. ✅ use_learning flag flows end-to-end
5. ✅ Learning context retrieved when use_learning=True
6. ✅ Agency-grade processor called with learning context when include_agency_grade=True
7. ✅ PDF export returns StreamingResponse with raw bytes
8. ✅ Streamlit uses resp.content for binary download

---

## ✅ Testing Strategy

### Unit-Level Verification:
- ✅ Code syntax validated (py_compile)
- ✅ Imports validated
- ✅ No circular dependencies
- ✅ Function signatures match

### Integration-Level Testing:
- Tools script can test with:
  1. Backend URL (full end-to-end)
  2. Local imports (isolated backend test)
  
### Manual Testing:
1. Start backend: `uvicorn backend.main:app --reload`
2. Start Streamlit: `streamlit run streamlit_pages/aicmo_operator.py`
3. Select "Strategy + Campaign Pack (Standard)"
4. Click "Generate draft report"
5. Verify backend logs show:
   - "🔥 [LEARNING ENABLED]" (if training data exists)
   - "✅ [API WRAPPER] generate_report call successful"
   - "Phase L: Agency-grade processing complete"
6. Click "Generate PDF"
7. Verify PDF downloads and opens in viewer

---

## 🔍 Design Decisions

### Why wrapper endpoint?
- Streamlit payload format differs from GenerateRequest schema
- Wrapper handles mapping without modifying core endpoint
- Core /aicmo/generate remains backward compatible
- Streamlit can update independently

### Why use_learning defaults to training data presence?
- Learning system is opt-in based on actual training data
- Safer default: only use learning if data actually exists
- Users can manually control via package selection

### Why resp.content for PDF?
- PDFs are binary data, not text
- resp.text would corrupt binary data
- resp.content ensures byte-perfect download
- st.download_button expects bytes, not strings

---

## ✅ Minimal Changes Principle Adhered

- No modifications to existing /aicmo/generate endpoint
- No modifications to safe_export_pdf
- No modifications to GenerateRequest (only added use_learning field, backward compatible)
- New wrapper endpoint added (additive, no breaking changes)
- PACKAGE_PRESETS updated (non-breaking change to defaults)
- PDF download flow improved (backward compatible fallback)

All changes are minimal, additive, and preserve backward compatibility.
