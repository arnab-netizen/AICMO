# WOW/Pack Generation Fix - Comprehensive Implementation Plan

## Issues Identified

### 1. **Placeholder Generation Failure (CRITICAL)**
- **Problem:** `build_default_placeholders()` receives `req.brief.model_dump()` which flattens nested structures
- **Result:** Required placeholders like `brand_name`, `category`, `city` are missing or empty
- **Impact:** `apply_wow_template()` detects <2 required fields and falls back to `fallback_basic`
- **Symptom:** All packs default to "fallback_basic" template instead of their actual templates

**Root cause in backend/services/wow_reports.py lines 169-176:**
```python
required_fields = ["brand_name", "category", "target_audience", "city"]
provided_fields = sum(1 for field in required_fields if placeholder_values.get(field) ...)
if provided_fields < 2:
    package_key = "fallback_basic"  # ← Fallback triggered for any incomplete brief
```

**Solution:** Enhance `build_default_placeholders()` to properly extract nested fields from ClientInputBrief structure.

### 2. **Section Generator Attribute Access Errors (HIGH)**
- **Problem:** Section generators access attributes that don't exist on the brief model
- **Examples:**
  - `_gen_audience_segments()` line 446: `b.product_service` (doesn't exist; should be `req.brief.product_service.items[0].name`)
  - Generators assume flat structure, but ClientInputBrief is deeply nested
- **Result:** AttributeError → Error message in client output

**Solution:** Fix all ~39 section generators to access correct nested fields + wrap with try/except for graceful degradation.

### 3. **Missing Brief Grounding in Templates (HIGH)**
- **Problem:** WOW templates and section generators use generic placeholders and hardcoded B2B examples
- **Examples from launch_gtm:**
  - "Micro-Influencer Partners: Thought leaders in {{category}}" (generic)
  - Persona: "Morgan Lee" (B2B, not B2C skincare)
  - No mention of actual brief content (Mumbai, organic, dermatologist-friendly, etc.)
  - Uses "your industry" and "your category" placeholders

**Solution:** 
1. Inject full brief context into LLM prompts for agency-grade sections
2. Update hardcoded templates to use actual brief fields
3. Add explicit system rules to avoid generic/B2B output for launch_gtm

### 4. **Placeholder Leakage in Final Output (MEDIUM)**
- **Problem:** Unfilled {{}} and [[]] placeholders, plus template markers leak to client
- **Examples:**
  - `{{overview}}` (template variable not filled)
  - `[Brand Name]`, `[Founder Name]` (unfilled bracket placeholders)
  - `{brand_name}`, `{product_service}` (unfilled curly placeholders)
  - `[This section was missing. AICMO auto-generated it...]` (system marker)

**Solution:**
1. Ensure all template placeholders are filled before returning to client
2. Sanitize final report to remove internal markers
3. Apply placeholder cleanup utility as final step in pipeline

### 5. **Learning System Not Gated (MEDIUM)**
- **Problem:** `learn_from_report()` can learn from broken reports with errors, placeholders, etc.
- **Result:** Contaminated learning DB that spreads bad patterns

**Solution:** Implement `is_report_learnable()` gate that rejects reports with errors, placeholders, or system markers before learning.

## Fix Implementation Order

1. **Fix placeholder generation** → Properly extract nested brief fields
2. **Wrap section generators** → Add try/except and graceful fallbacks
3. **Ground launch_gtm pack** → Inject brief context into prompts
4. **Sanitize final output** → Remove template markers and placeholders
5. **Gate learning system** → Reject bad reports before learning
6. **Test all packs** → Verify no regressions

## Files to Modify

### Backend Core
- `backend/services/wow_reports.py` - Fix `build_default_placeholders()`, enhance placeholder extraction
- `backend/main.py` - Wrap section generators, add error handling, ground launch_gtm
- `backend/agency_grade_enhancers.py` - Add brief grounding to TURBO sections
- `aicmo/generators/language_filters.py` - Add final report sanitizer
- `aicmo/io/client_reports.py` - Add helper to extract nested brief fields

### Tests to Create
- `backend/tests/test_wow_pack_grounding.py` - Verify brief grounding works
- `backend/tests/test_placeholder_cleanup.py` - Verify no leakage
- `backend/tests/test_report_learnable_gate.py` - Verify learning gate works
- `backend/tests/test_all_packs_quality.py` - Scan all pack outputs

### Scripts
- `scripts/test_all_packs_quality.py` - Quality check for all packs
- `scripts/verify_launch_gtm_skincare.sh` - End-to-end test with skincare brief

## Success Criteria

For each pack:
- ✅ No `[Brand Name]`, `[Founder Name]`, `{brand_name}` placeholders
- ✅ No "your industry", "your category" generic phrases
- ✅ No "Error generating", "object has no attribute", traceback strings
- ✅ No "[This section was missing...]" markers
- ✅ No B2B personas for B2C packs (no "Morgan Lee" for skincare)
- ✅ Brief grounding: actual industry/audience/goals present in output
- ✅ All required sections present (not empty)
- ✅ Learning gate rejects broken reports

## Implementation Timeline

Phase 1 (Critical): Placeholder generation + section generator wrapping → 45 min
Phase 2 (Important): Launch_gtm grounding + final sanitization → 30 min  
Phase 3 (Safety): Learning gate + comprehensive tests → 25 min
Phase 4 (Validation): Full test suite + smoke checks → 20 min

Total: ~2-2.5 hours for production-ready fixes
