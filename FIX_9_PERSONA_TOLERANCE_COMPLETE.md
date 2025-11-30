# FIX #9: Make Persona Fields Tolerant (No More 500s)

**Date:** November 29, 2025  
**Commit:** `47b5fe4`  
**Status:** ✅ COMPLETE & COMMITTED

---

## Problem

HTTP 500 errors when LLM returns partial persona data:
- `ValidationError: persona_cards.0.demographics Field required`
- `ValidationError: persona_cards.0.psychographics Field required`
- `ValidationError: persona_cards.0.tone_preference Field required`

**Root Cause:** PersonaCard model had required fields that LLM doesn't always generate.

---

## Solution

### 1. Made PersonaCard Fields Tolerant

**File:** `aicmo/io/client_reports.py`

Changed from:
```python
class PersonaCard(BaseModel):
    name: str
    demographics: str          # Required → causes 500 if missing
    psychographics: str        # Required → causes 500 if missing
    tone_preference: str       # Required → causes 500 if missing
```

To:
```python
class PersonaCard(BaseModel):
    # Required headline fields
    name: str
    
    # Optional fields with safe defaults
    demographics: str = ""
    psychographics: str = ""
    tone_preference: str = ""
    pain_points: List[str] = Field(default_factory=list)
    triggers: List[str] = Field(default_factory=list)
    objections: List[str] = Field(default_factory=list)
    content_preferences: List[str] = Field(default_factory=list)
    primary_platforms: List[str] = Field(default_factory=list)
```

**Impact:** Validation now accepts partial persona data without throwing errors.

---

### 2. Added Normalization Block in main.py

**File:** `backend/main.py` (lines 3087-3111)

Before `AICMOOutputReport` instantiation, normalize all persona dicts:

```python
# Normalize persona_cards before instantiation to handle partial LLM-generated personas
if persona_cards:
    normalised_personas = []
    for p in persona_cards:
        if not isinstance(p, dict):
            continue
        normalised_personas.append({
            "name": p.get("name") or "Primary Persona",
            "demographics": p.get("demographics", ""),
            "psychographics": p.get("psychographics", ""),
            "tone_preference": p.get("tone_preference", ""),
            "pain_points": p.get("pain_points", []),
            "triggers": p.get("triggers", []),
            "objections": p.get("objections", []),
            "content_preferences": p.get("content_preferences", []),
            "primary_platforms": p.get("primary_platforms", []),
        })
    persona_cards = normalised_personas
```

**Impact:** Ensures Pydantic always receives complete dicts with all required keys, preventing validation failures.

---

### 3. Created Regression Test

**File:** `backend/tests/test_output_report_persona_validation.py`

6 test functions covering:

1. **test_persona_card_allows_missing_fields** – PersonaCard works with only `name` field
2. **test_output_report_allows_partial_persona_cards** – Partial persona data in AICMOOutputReport
3. **test_output_report_partial_personas_with_some_fields** – Preserves present fields, defaults missing ones
4. **test_output_report_empty_persona_cards_list** – Empty list accepted
5. **test_output_report_persona_cards_omitted** – Field completely omitted defaults to []
6. **test_persona_card_serialization_with_defaults** – Serializes cleanly with defaults

**Status:** ✅ All 6 tests passing

---

## Test Results

### New Tests
```
backend/tests/test_output_report_persona_validation.py
✅ test_persona_card_allows_missing_fields
✅ test_output_report_allows_partial_persona_cards
✅ test_output_report_partial_personas_with_some_fields
✅ test_output_report_empty_persona_cards_list
✅ test_output_report_persona_cards_omitted
✅ test_persona_card_serialization_with_defaults

6 passed in 6.45s
```

### Existing Tests (No Regressions)
```
backend/tests/test_generate_request_personas.py
✅ 3 tests passing

backend/tests/test_export_pdf_validation.py
✅ 9 tests passing

backend/tests/test_api_endpoint_integration.py
✅ 3/4 passing (1 pre-existing failure in BrandBrief)
```

---

## How It Works

### Scenario 1: Complete Persona from LLM
```python
persona_dict = {
    "name": "Executive Emma",
    "demographics": "50-60, C-level",
    "psychographics": "Results-driven, strategic",
    "tone_preference": "Direct, professional",
    ...
}
# ✅ Passes through normalization unchanged, validates successfully
```

### Scenario 2: Partial Persona from LLM
```python
persona_dict = {
    "name": "Remote Rachel",
    # Missing: demographics, psychographics, tone_preference
}
# Normalization adds defaults:
{
    "name": "Remote Rachel",
    "demographics": "",          # ← Default added
    "psychographics": "",        # ← Default added
    "tone_preference": "",       # ← Default added
    "pain_points": [],
    ...
}
# ✅ Validation passes, no 500 error
```

### Scenario 3: Missing Field in Industry Config
```python
industry_persona = {
    "name": "B2B Buyer",
    "role": "Procurement Manager",
    # Missing demographics, psychographics fields
}
# After normalization in main.py:
{
    "name": "B2B Buyer",
    "demographics": "",          # ← Default added
    "psychographics": "",        # ← Default added
    ...
}
# ✅ Validation passes
```

---

## Benefits

| Benefit | Impact |
|---------|--------|
| **No 500 errors on partial data** | Users don't hit validation crashes when LLM skips fields |
| **Tolerant schema** | LLM can return incomplete personas safely |
| **Ship now, fix later** | Don't wait for perfect LLM personas – iterate on other features |
| **Backward compatible** | Complete personas still work perfectly |
| **Defensive coding** | Multiple layers: tolerant model + normalization |

---

## Architecture Pattern

This implements a **tolerant output model** pattern:

```
LLM Output (Partial)
    ↓
Normalization Layer (fills gaps)
    ↓
Pydantic Model (validates, never fails)
    ↓
AICMOOutputReport (complete, valid)
```

**Key principle:** Fail early in normalization (never crash), not in validation.

---

## Deployment Notes

### Backward Compatibility
- ✅ No breaking changes to API contracts
- ✅ Complete personas still serialize identically
- ✅ Partial personas now serialize safely

### Database/Storage
- ✅ Persona fields with empty strings serialize to JSON cleanly
- ✅ No database schema changes required
- ✅ Safe to deploy immediately

### Monitoring
- When personas are normalized with defaults, consider logging:
  ```python
  if not original_demographics and p.get("demographics") == "":
      logger.info(f"Persona '{name}' missing demographics, using default")
  ```

---

## Files Changed

```
aicmo/io/client_reports.py
├─ PersonaCard class (7 fields now have defaults)

backend/main.py
├─ Added normalization block (line 3087-3111)
├─ ~25 lines added

backend/tests/test_output_report_persona_validation.py
├─ NEW file
├─ 6 test functions
├─ 100+ lines
```

---

## Next Steps (Optional Improvements)

1. **Add logging** when personas are normalized with defaults
2. **Monitor** which LLM providers skip persona fields
3. **Improve LLM prompts** to encourage complete persona generation
4. **Add metrics** to track partial vs. complete personas

---

## Summary

FIX #9 makes the PersonaCard schema **tolerant of partial LLM data** by:
- Making optional fields have safe defaults
- Adding normalization layer to fill gaps
- Creating 6 regression tests to prevent regressions

**Result:** No more 500 errors on persona validation. Users can generate reports with industry personas or partial LLM output safely.

**Commit:** `47b5fe4` pushed to origin/main ✅
