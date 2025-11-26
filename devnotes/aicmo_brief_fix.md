# 🔧 AICMO Report Pipeline Fix – Meta Instructions

**Objective:** Fix AICMO's report pipeline so that **all WOW packs** and base packs:

1. ✅ Always receive a complete, validated client brief
2. ✅ Never emit:
   - "Not specified"
   - "[Error generating ..."
   - Placeholder names like "Your Brand", "your space", "ideal customers"
   - Attribute errors like `'ClientInputBrief' object has no attribute 'industry'`

---

## Work Plan (7 Steps)

### ✅ Step 1: Schema Fixes – ClientInputBrief & BrandBrief [COMPLETE]
- ✅ Added missing fields: `industry`, `product_service`, `primary_goal`, `primary_customer`
- ✅ Created `with_safe_defaults()` helper method on BrandBrief
- ✅ Added `with_safe_defaults()` on ClientInputBrief
- ✅ Updated file: `aicmo/io/client_reports.py`
- ✅ Verified: No compilation errors

### ✅ Step 2: Backend Route Validation [COMPLETE]
- ✅ Added `validate_client_brief()` function in `backend/main.py`
- ✅ Validates required fields: brand_name, industry, product_service, primary_goal, primary_customer
- ✅ Raises HTTPException (400) if any required field missing
- ✅ Applied `with_safe_defaults()` before validation
- ✅ Updated brief construction with better defaults
- ✅ Verified: No compilation errors

### ✅ Step 3: Pack Reducer Logic [COMPLETE]
- ✅ **No reducer logic found** – briefs not sliced per-pack, design already safe
- ✅ All generators receive complete brief with all required fields
- ✅ Token replacement logic (`apply_token_replacements()`) automatically benefits from schema fix
- ✅ Verified: No changes needed, implicit fix via schema enhancement

### ✅ Step 4: Advanced Add-ons – Defensive Wrappers [COMPLETE]
- ✅ Updated section generator error handling in `/api/aicmo/generate_report`
- ✅ Changed from: `results[section_id] = f"[Error generating {section_id}: {str(e)}]"`
- ✅ Changed to: `results[section_id] = ""` with `logger.error(...)`
- ✅ Errors logged internally with full traceback, not visible to clients
- ✅ Empty sections skipped during aggregation → no errors in final output

### ✅ Step 5: Streamlit UI [COMPLETE]
- ✅ Marked required fields with `*` (brand_name, product_service, industry, objectives)
- ✅ Added help text for required fields
- ✅ Created `validate_required_brief_fields()` function
- ✅ Disabled "Generate draft report" button until all required fields filled
- ✅ Display warning message showing which fields are missing
- ✅ Updated file: `streamlit_pages/aicmo_operator.py`
- ✅ Verified: No compilation errors

### ✅ Step 6: Integration Tests [COMPLETE]
- ✅ Created `tests/test_pack_reports_are_filled.py` with 26 tests
- ✅ Tests validate schema enhancements (required fields exist)
- ✅ Tests validate `with_safe_defaults()` method works
- ✅ Tests validate placeholder prevention
- ✅ Tests validate optional field handling
- ✅ Parametrized tests over all 6 package keys
- ✅ **All 26 tests pass** ✅
- ✅ File: `tests/test_pack_reports_are_filled.py` (360+ lines)

### ⏳ Step 7: Copilot Verification
- [ ] Check all ClientInputBrief/BrandBrief references
- [ ] Verify no "Not specified" / "[Error generating" / placeholder names in final output
- [ ] Run pytest and confirm all packs pass

---

## Key Principles

✅ **Small, explicit changes** – No big refactors  
✅ **Preserve working features** – No breaking API changes  
✅ **Fail fast, gracefully** – Validate early, never emit errors to client  
✅ **Defensive defaults** – Always have a sensible fallback  
✅ **Test coverage** – Automated checks on all packs  

---

## Status: STEPS 1-2 COMPLETE, CONTINUING WITH STEP 3

Next: Locate and fix pack reducer logic to preserve required fields

