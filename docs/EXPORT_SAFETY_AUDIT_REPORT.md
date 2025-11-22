# Export Safety Audit Report

**Date**: 2024  
**Scope**: Comprehensive verification that AICMOOutputReport exports (PDF/PPTX/ZIP) either validate properly or are explicitly accepted as safe.  
**Finding**: **2 RISKY PATHS IDENTIFIED** - PDF export can bypass placeholder validation.

---

## Executive Summary

| Export Type | API Endpoint | Function | Validation | Status |
|-------------|-------------|----------|-----------|--------|
| PDF | POST /aicmo/export/pdf | safe_export_pdf() | ❌ NOT CALLED | 🔴 RISKY |
| PPTX | POST /aicmo/export/pptx | safe_export_pptx() | ✅ CALLED | ✅ SAFE |
| ZIP | POST /aicmo/export/zip | safe_export_zip() | ✅ CALLED | ✅ SAFE |

---

## Detailed Analysis

### 1. PDF Export - 🔴 RISKY

**Entry Points:**
- **API Endpoint**: `POST /aicmo/export/pdf` (backend/main.py:862-880)
- **Streamlit Path**: `aicmo_export()` in streamlit_app.py:320-352 → calls API endpoint

**Code Path Analysis:**

```
User Request: POST /aicmo/export/pdf {"markdown": "..."}
   ↓
aicmo_export_pdf(payload) [backend/main.py:862]
   Line 873: result = safe_export_pdf(markdown)     ← NO check_placeholders parameter!
   ↓
safe_export_pdf(markdown, check_placeholders=False) [backend/export_utils.py:81]
   Line 94-99: Checks if markdown empty ✅
   Line 106-125: Placeholder detection IF check_placeholders=True ❌ SKIPPED (False by default)
   Line 127: Generates PDF from markdown
   Line 135-147: Returns StreamingResponse
```

**Root Cause:**
- `safe_export_pdf()` has signature: `def safe_export_pdf(markdown: str, check_placeholders: bool = False)`
- `aicmo_export_pdf()` calls it as: `result = safe_export_pdf(markdown)` (no 2nd parameter)
- Result: `check_placeholders` defaults to `False`
- When `False`, placeholder validation (lines 106-125) is **skipped entirely**

**Validation That IS Performed:**
- ✅ Line 94-99: Empty markdown check
- ✅ Line 127: text_to_pdf_bytes() - basic PDF generation

**Validation That IS NOT Performed:**
- ❌ Lines 106-125: Placeholder detection (9 patterns checked - "TBD", "PLACEHOLDER", "Hook idea for day", "Performance review will be populated", etc.)
- ❌ No report-level validation (unlike PPTX/ZIP)

**Risk Level:**
- 🔴 **CRITICAL** - User can export PDF with stub placeholders left in content
- If AICMOOutputReport contains unresolved sections, they export to PDF without detection

**Example Scenarios:**
```
Input: markdown = "Campaign Strategy:\n[PLACEHOLDER]\n\nBudget: TBD\n..."
Output: PDF file generated with placeholders visible
Expected: Validation error blocking export
Actual: PDF exports successfully with stubs intact
```

---

### 2. PPTX Export - ✅ SAFE

**Entry Points:**
- **API Endpoint**: `POST /aicmo/export/pptx` (backend/main.py:885-911)
- **Streamlit Path**: `aicmo_export()` in streamlit_app.py:320-352 → calls API endpoint

**Code Path Analysis:**

```
User Request: POST /aicmo/export/pptx {"brief": {...}, "output": {...}}
   ↓
aicmo_export_pptx(payload) [backend/main.py:885]
   Line 911: result = safe_export_pptx(brief, output)     ← Uses default check_placeholders
   ↓
safe_export_pptx(brief, output, check_placeholders=True) [backend/export_utils.py:169]
   Line 197-203: Calls _validate_report_for_export(output) if check_placeholders=True ✅ CALLED
   ↓
_validate_report_for_export(output) [backend/export_utils.py:36]
   Line 37: validate_report(output) → returns list of validation_issues
   Line 53: errors = [i for i in validation_issues if i.severity == "error"]
   Line 63: Returns error dict if blocking issues found
   ↓
If validation passes:
   Line 211+: PPTX generation proceeds
   Line 235+: Returns StreamingResponse
```

**Validation That IS Performed:**
- ✅ Line 197-203: Comprehensive validation via `_validate_report_for_export()`
  - Calls `validate_report()` → full report validation
  - Calls `has_blocking_issues()` → severity filtering ("error" level blocks export)
  - Returns error dict if validation fails
- ✅ Line 205-207: Checks marketing_plan/campaign_blueprint not None
- ✅ Error returns immediately if validation fails (line 203)

**Default Parameters:**
- ✅ `check_placeholders: bool = True` (line 172) — validation is ENABLED by default
- ✅ This means PPTX export ALWAYS validates before returning

**Risk Level:**
- ✅ **SAFE** - Comprehensive validation with correct defaults

---

### 3. ZIP Export - ✅ SAFE

**Entry Points:**
- **API Endpoint**: `POST /aicmo/export/zip` (backend/main.py:918-950)
- **Streamlit Path**: `aicmo_export()` in streamlit_app.py:320-352 → calls API endpoint

**Code Path Analysis:**

```
User Request: POST /aicmo/export/zip {"brief": {...}, "output": {...}}
   ↓
aicmo_export_zip(payload) [backend/main.py:918]
   Line 947: result = safe_export_zip(brief, output)     ← Uses default check_placeholders
   ↓
safe_export_zip(brief, output, check_placeholders=True) [backend/export_utils.py:442]
   Line 462-466: Calls _validate_report_for_export(output) if check_placeholders=True ✅ CALLED
   ↓
_validate_report_for_export(output) [backend/export_utils.py:36]
   Line 37: validate_report(output) → returns list of validation_issues
   Line 53: errors = [i for i in validation_issues if i.severity == "error"]
   Line 63: Returns error dict if blocking issues found
   ↓
If validation passes:
   Line 470+: Markdown generation
   Line 475+: ZIP file creation with report, personas, creatives
   Line 520+: Returns StreamingResponse
```

**Validation That IS Performed:**
- ✅ Line 462-466: Comprehensive validation via `_validate_report_for_export()`
  - Same validation chain as PPTX
  - Returns error dict if validation fails
- ✅ Line 454-461: Checks brief/output not None
- ✅ Line 468-482: Checks markdown not empty
- ✅ Error returns immediately if validation fails (line 465)

**Default Parameters:**
- ✅ `check_placeholders: bool = True` (line 444) — validation is ENABLED by default
- ✅ This means ZIP export ALWAYS validates before returning

**Risk Level:**
- ✅ **SAFE** - Comprehensive validation with correct defaults

---

## Validation Infrastructure

### _validate_report_for_export() - backend/export_utils.py:36-79

```python
def _validate_report_for_export(output: AICMOOutputReport) -> Optional[Dict[str, str]]:
    """Validate report before export to ensure high quality."""
    
    # Line 37: Get all validation issues
    validation_issues = validate_report(output)
    
    # Line 53: Filter to only "error" severity (blocks export)
    errors = [i for i in validation_issues if i.severity == "error"]
    
    # Line 63: Return error dict if blocking issues found
    if errors:
        return {
            "error": True,
            "message": "...",
            "blocked_by": [e.message for e in errors],
            "export_type": "...",
        }
    
    return None  # All valid
```

**Severity Filtering Logic:**
- Only issues with `severity == "error"` block export
- Warnings and info-level issues do not block export
- Proper implementation - not overly strict

---

## Summary of Findings

### Paths Verified

| Path | Validation | Call Chain | Status |
|------|-----------|-----------|--------|
| PDF API Endpoint | ❌ None | aicmo_export_pdf → safe_export_pdf(check_placeholders=False) | 🔴 RISKY |
| PPTX API Endpoint | ✅ Full | aicmo_export_pptx → safe_export_pptx(check_placeholders=True) → _validate_report_for_export() | ✅ SAFE |
| ZIP API Endpoint | ✅ Full | aicmo_export_zip → safe_export_zip(check_placeholders=True) → _validate_report_for_export() | ✅ SAFE |
| Streamlit PDF | ❌ None | aicmo_export() → API endpoint → same as PDF above | 🔴 RISKY |
| Streamlit PPTX | ✅ Full | aicmo_export() → API endpoint → same as PPTX above | ✅ SAFE |
| Streamlit ZIP | ✅ Full | aicmo_export() → API endpoint → same as ZIP above | ✅ SAFE |

---

## Exact Code References

### RISKY: PDF Export Without Validation

**File**: backend/main.py  
**Function**: `aicmo_export_pdf()`  
**Lines**: 862-880

```python
@app.post("/aicmo/export/pdf")
def aicmo_export_pdf(payload: dict):
    """Convert markdown to PDF with safe error handling."""
    markdown = payload.get("markdown") or ""
    result = safe_export_pdf(markdown)  # ← LINE 873: NO check_placeholders=True
    
    if isinstance(result, dict):
        logger.warning(f"PDF export failed: {result}")
        return JSONResponse(status_code=400, content=result)
    
    return result
```

**Problem**: Line 873 calls `safe_export_pdf(markdown)` without `check_placeholders=True` parameter.

**Required Fix**:
```python
result = safe_export_pdf(markdown, check_placeholders=True)
```

---

### SAFE: PPTX Export With Validation

**File**: backend/main.py  
**Function**: `aicmo_export_pptx()`  
**Lines**: 885-911

```python
@app.post("/aicmo/export/pptx")
def aicmo_export_pptx(payload: dict):
    """Convert brief + output to PPTX with safe error handling."""
    # ... input validation ...
    result = safe_export_pptx(brief, output)  # ← Uses default check_placeholders=True
    # ... error handling ...
    return result
```

**Safe**: Uses default parameter which is `True`.

---

### SAFE: ZIP Export With Validation

**File**: backend/main.py  
**Function**: `aicmo_export_zip()`  
**Lines**: 918-950

```python
@app.post("/aicmo/export/zip")
def aicmo_export_zip(payload: dict):
    """Export ZIP with safe error handling."""
    # ... input validation ...
    result = safe_export_zip(brief, output)  # ← Uses default check_placeholders=True
    # ... error handling ...
    return result
```

**Safe**: Uses default parameter which is `True`.

---

## Recommendations

### Priority 1 (CRITICAL)

**Issue**: PDF export bypasses placeholder validation

**Fix Location**: backend/main.py:873

**Change**:
```python
# BEFORE (RISKY)
result = safe_export_pdf(markdown)

# AFTER (SAFE)
result = safe_export_pdf(markdown, check_placeholders=True)
```

**Rationale**: 
- Brings PDF validation to parity with PPTX/ZIP
- Prevents exporting content with [TBD], [PLACEHOLDER], etc.
- Safe change - only adds validation, no breaking changes

**Testing**:
```python
# Add test: PDF export should be blocked if markdown contains placeholders
def test_aicmo_export_pdf_with_placeholders():
    payload = {"markdown": "Content with [PLACEHOLDER] placeholder"}
    response = client.post("/aicmo/export/pdf", json=payload)
    assert response.status_code == 400
    assert "error" in response.json()
```

---

## Audit Completion Status

| Task | Status | Evidence |
|------|--------|----------|
| Map all export functions | ✅ Complete | 5 functions identified: safe_export_{pdf,pptx,zip}, aicmo_export_{pdf,pptx,zip} |
| Examine validation logic | ✅ Complete | _validate_report_for_export() properly implements severity filtering |
| Trace API endpoint calls | ✅ Complete | All 3 API endpoints examined; call chains documented |
| Verify Streamlit paths | ✅ Complete | Streamlit aicmo_export() calls API endpoints (no direct calls) |
| Identify risky paths | ✅ Complete | 1 RISKY path: PDF export (aicmo_export_pdf → safe_export_pdf without validation) |
| Verify safe paths | ✅ Complete | 2 SAFE paths: PPTX/ZIP exports use validation by default |
| Create audit report | ✅ Complete | This document |

---

## Conclusion

**Finding**: PDF export can export AICMOOutputReport with placeholder stubs present, while PPTX and ZIP exports validate first.

**Root Cause**: `aicmo_export_pdf()` calls `safe_export_pdf(markdown)` without `check_placeholders=True` parameter.

**Risk Level**: 🔴 CRITICAL for data quality (stubs leak to export)

**Confidence Level**: ✅ HIGH - Code review complete, exact line numbers provided, fix is straightforward

**Recommended Action**: Apply Priority 1 fix above to backend/main.py:873
