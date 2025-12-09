# 4-Layer Generation Pipeline - Implementation Plan

**Date:** 2025-12-09  
**Status:** Planning Phase  
**Baseline Tests:** 1029 passing ✅

---

## Executive Summary

We are implementing a **4-layer generation system** into the existing AICMO pipeline to:
1. **NEVER block** on benchmark/quality failures → no more 500 errors
2. **Always return output** for every requested section (even if imperfect)
3. **Improve quality progressively** through humanization and targeted rewrites
4. **Maintain backward compatibility** with all existing APIs and callers

---

## Current Architecture (Status Quo)

```
api_aicmo_generate_report(payload)
  ↓
generate_sections(section_ids, req, mp, cb, cal, pr, creatives, action_plan)
  ↓
  PASS 1: For each section_id
    ├─ Stub mode? → _stub_section_for_pack()
    └─ Normal? → SECTION_GENERATORS[section_id](**context)
  ↓
  PASS 1.5: Quick Social cleanup
  ↓
  QUALITY GATE: enforce_benchmarks_with_regen()
    ├─ Validate sections
    ├─ Regenerate failed sections
    └─ On failure → raise HTTPException(500) ❌ PROBLEM
  ↓
  Return results dict
```

**Problems:**
- ❌ Benchmark failures → 500 errors that block users
- ❌ No structured quality scoring
- ❌ No humanization pass
- ❌ Brittle calendar generation (fails whole pack)
- ❌ No section-level rewrite capability

---

## New 4-Layer Architecture (Proposed)

```
generate_sections(section_ids, req, mp, cb, cal, pr, creatives, action_plan)
  ↓
  For each section_id in section_ids:
    ↓
    LAYER 1: generate_raw_section(section_id, context)
      • Call existing SECTION_GENERATORS[section_id]
      • Focus on correct structure + outline + word-count ranges
      • NO validation, NO blocking
      • Returns: raw_text (str)
    ↓
    LAYER 2: enhance_section_humanizer(section_id, raw_text, context)
      • 2nd LLM call to improve tone, specificity, hooks
      • Preserve structure and headings
      • On error → return raw_text (fallback, no exception)
      • Returns: enhanced_text (str)
    ↓
    LAYER 3: run_soft_validators(section_id, enhanced_text, context)
      • Structural checks (headings, required fields)
      • Placeholder detection (no "TBD", "[insert]")
      • Genericity scoring (flag clichés)
      • Length bounds checking
      • Returns: (text, quality_score, genericity_score, warnings)
      • ❌ NEVER raise HTTPException, only log
    ↓
    LAYER 4: (Optional, based on Layer 3 scores)
      • If quality_score < 70 OR specific warnings:
        • rewrite_low_quality_section(section_id, text, warnings, context)
        • Max 1 attempt
        • On error → use Layer 3 output as fallback
      • Returns: final_text (str)
    ↓
    results[section_id] = final_text
  ↓
  Return results dict (all sections present, no 500s)
```

**Benefits:**
- ✅ NO MORE 500 ERRORS from quality issues
- ✅ Structured quality scoring & warnings
- ✅ Progressive improvement via humanization
- ✅ Optional section-level fixes
- ✅ All sections always returned

---

## Files to Create

### 1. `backend/layers/__init__.py`
- New module for all 4-layer functions
- Minimal init file

### 2. `backend/layers/layer1_raw_draft.py`
**Purpose:** LAYER 1 - Raw draft generator (unblocked)

**Functions:**
```python
def generate_raw_section(
    section_id: str,
    context: dict,
    req: GenerateRequest,
) -> str:
    """
    Generate first-pass draft for a section.
    
    - Uses existing SECTION_GENERATORS[section_id]
    - Focus on structure + outline + word-count ranges
    - No validation, no exceptions
    - Returns raw content or empty string
    """
```

**Modifications to individual generators** (e.g., `_gen_overview`, `_gen_campaign_objective`):
- Update prompts to include **explicit outline** with section headings
- Add **word-count ranges** (e.g., "80–120 words"), not exact counts
- Ensure prompts are deterministic and clear

**Example prompt structure:**
```
You are a strategic marketing expert. Generate a clear, well-structured [SECTION_NAME].

OUTLINE:
- Heading 1: [Purpose] (150–200 words)
- Heading 2: [Purpose] (100–150 words)
- Heading 3: [Purpose] (80–120 words)

CONTEXT:
- Brand: {brand_name}
- Goal: {goal}
- Audience: {audience}
- Pain points: {pain_points}

INSTRUCTIONS:
- Use clear, professional language
- Include specific details from the context
- Maintain professional tone throughout
- No placeholders like "TBD", "[insert]", etc.

Output ONLY the content, no explanations.
```

---

### 3. `backend/layers/layer2_humanizer.py`
**Purpose:** LAYER 2 - Humanization/enhancement pass (fallback-safe)

**Functions:**
```python
def enhance_section_humanizer(
    section_id: str,
    raw_text: str,
    context: dict,
    req: GenerateRequest,
) -> str:
    """
    Improve draft for human readability and specificity.
    
    - Takes raw_text from Layer 1
    - Calls LLM to:
      * Eliminate generic phrases and clichés
      * Improve clarity, flow, storytelling
      * Add specific details from context
      * Strengthen hooks, CTAs, transitions
      * Maintain structure and outline
      * Respect word-count ranges (±20% tolerance)
    - On ANY error (timeout, API fail, parse fail) → return raw_text
    - NEVER raise exceptions to caller
    - Returns enhanced content (or raw as fallback)
    """
```

**Humanizer prompt example:**
```
You are a world-class copywriter improving marketing content.

TASK: Enhance the following content to be more human, specific, and compelling.

IMPROVEMENTS NEEDED:
1. Remove generic phrases ("boost your brand", "drive engagement", "level up")
2. Add specific details from the brief and context provided
3. Improve hooks and CTAs (make them concrete actions, not generic)
4. Strengthen transitions and flow
5. Add credibility markers (specific numbers, examples where possible)

CONSTRAINTS:
- Maintain exact same structure and headings
- Keep sections within ±20% of original word count
- No placeholders like "TBD", "[insert]"
- Professional, authoritative tone

ORIGINAL CONTENT:
{raw_text}

CONTEXT:
- Brand: {brand_name}
- Goal: {goal}
- Audience: {audience}
- {additional context}

ENHANCED CONTENT (same structure, more specific & compelling):
```

---

### 4. `backend/layers/layer3_soft_validators.py`
**Purpose:** LAYER 3 - Soft validators (non-blocking scoring & flagging)

**Functions:**
```python
def run_soft_validators(
    pack_key: str,
    section_id: str,
    content: str,
    context: dict,
) -> tuple[str, float, float, list[str]]:
    """
    Score and flag issues without blocking.
    
    Returns:
        (content, quality_score, genericity_score, warnings)
    
    quality_score: 0–100 (based on structure, length, placeholders)
    genericity_score: 0–100 (0=very generic, 100=very specific)
    warnings: list of warning codes, e.g.:
        ["missing_cta", "too_generic_hooks", "too_short", "placeholder_detected"]
    
    CRITICAL: This function must NEVER raise HTTPException or any exception
    that bubbles up to the API. All errors caught internally and logged.
    """
```

**Sub-validators (internal):**
```python
def _check_structural_integrity(section_id: str, content: str, pack_key: str) -> dict:
    """Check required headings, fields, structure."""
    # Verify required sections exist
    # Check for markdown structure
    # Return: { "passed": bool, "missing_fields": [...] }

def _check_placeholders(content: str) -> dict:
    """Detect "TBD", "[insert]", "[specify]", etc."""
    # Pattern match against placeholder list
    # Return: { "has_placeholders": bool, "found": [...] }

def _check_genericity(content: str) -> dict:
    """Flag overly generic phrases."""
    # Pattern match against cliché list
    # Return: { "genericity_score": 0–100, "generic_phrases": [...] }

def _check_length_bounds(section_id: str, content: str, expected_range: tuple) -> dict:
    """Check word count is reasonable."""
    # Word count analysis
    # Return: { "in_range": bool, "word_count": int, "expected": (min, max) }
```

**Cliché/Generic patterns to detect:**
```python
GENERIC_PATTERNS = [
    r"\bboost\s+(?:your\s+)?brand\b",
    r"\blevel\s+up\b",
    r"\bdrive\s+engagement\b",
    r"\bincrease\s+awareness\b",
    r"\bstay\s+ahead\s+of\s+the\s+curve\b",
    r"\bthink\s+outside\s+the\s+box\b",
    r"\bsynergize\b",
    r"\binnovative\s+solution\b",
    r"\bworld\s+class\b",
    r"\bleading\s+edge\b",
]
```

---

### 5. `backend/layers/layer4_section_rewriter.py`
**Purpose:** LAYER 4 - Optional section-level rewrites (non-blocking)

**Functions:**
```python
def rewrite_low_quality_section(
    pack_key: str,
    section_id: str,
    content: str,
    warnings: list[str],
    context: dict,
    req: GenerateRequest,
) -> str:
    """
    Rewrite weak sections to improve quality.
    
    - Triggered if quality_score < 70 or specific warnings present
    - Single LLM call to rewrite the section
    - Preserve structure and headings
    - Fix issues indicated by warnings
    - On ANY error → return original content (no exception)
    - NEVER block
    
    Returns improved content (or original on error)
    """
```

**Rewrite prompt structure:**
```
You are a strategic marketing expert tasked with improving section quality.

CURRENT CONTENT (has issues):
{content}

ISSUES TO FIX:
{warnings_description}
- Too generic: remove clichés like "boost your brand"
- Missing specificity: add concrete details from context
- Weak hooks: make CTAs actionable and specific
- Unclear transitions: strengthen connections between ideas

CONTEXT:
- Brand: {brand_name}
- Goal: {goal}
- Audience: {audience}

REQUIREMENTS:
- Maintain exact same structure and headings
- Keep word count within ±20% of original
- Make content specific, not generic
- Strong, actionable CTAs
- Professional tone

IMPROVED CONTENT (fixed issues, same structure):
```

---

## Files to Modify

### 1. `backend/main.py` - `generate_sections(...)`
**Line:** ~6812

**Changes:**
- Add loop to wire all 4 layers
- Import new layer modules
- Remove old `enforce_benchmarks_with_regen` call (or make it optional/soft)
- Collect final sections with quality metadata

**New flow in generate_sections:**
```python
def generate_sections(...) -> dict[str, str]:
    """
    Generate content using 4-layer pipeline.
    
    - LAYER 1: Raw draft (structured, unblocked)
    - LAYER 2: Humanizer (improved tone, specific)
    - LAYER 3: Soft validators (scoring, warnings)
    - LAYER 4: Optional rewrites (based on scores)
    
    Returns dict[section_id → final_content]
    - ALL sections always present
    - NO HTTP 500 errors from quality issues
    """
    results = {}
    quality_metadata = {}  # Optional: track scores for logging/dashboards
    
    for section_id in section_ids:
        try:
            # LAYER 1: Raw draft
            raw_text = generate_raw_section(section_id, context, req)
            
            # LAYER 2: Humanizer
            enhanced_text = enhance_section_humanizer(section_id, raw_text, context, req)
            
            # LAYER 3: Soft validators
            final_text, quality_score, genericity_score, warnings = run_soft_validators(
                pack_key, section_id, enhanced_text, context
            )
            
            quality_metadata[section_id] = {
                "quality_score": quality_score,
                "genericity_score": genericity_score,
                "warnings": warnings,
            }
            
            # LAYER 4: Optional rewrite
            if quality_score < 70 or any(w in warnings for w in ["too_generic", "missing_hooks"]):
                final_text = rewrite_low_quality_section(
                    pack_key, section_id, final_text, warnings, context, req
                )
            
            results[section_id] = final_text
            
        except Exception as e:
            # Absolute fallback: log and return empty
            logger.error(f"4-layer pipeline failed for {section_id}: {e}")
            results[section_id] = ""
    
    return results
```

### 2. `backend/validators/report_enforcer.py` - Refactor to non-blocking
**Line:** ~60

**Changes:**
- Add `strict_mode` parameter (default False)
- When `strict_mode=False`:
  - Don't raise HTTPException on benchmark failures
  - Log warnings instead
  - Return sections as-is
- Keep existing function signature for backwards compatibility

**New approach:**
```python
def enforce_benchmarks_with_regen(
    ...,
    draft_mode: bool = False,
    strict_mode: bool = False,  # NEW: Soft validation mode
) -> EnforcementOutcome:
    """
    Soft enforcement mode (new default):
    - Run validation
    - Log warnings
    - Return sections as-is
    - NEVER raise 500 on content-only issues
    
    Strict mode (old behavior, opt-in):
    - Run validation
    - Regenerate failures
    - Raise 500 if still failing
    """
```

---

## Special Case: Social Calendar Hardening

**File:** `aicmo/generators/social_calendar_generator.py` (~200 lines)

**Problem:** Fails if LLM returns unparseable JSON or incomplete data

**Solution:** Multi-pass generation with fallback templates per day

```python
def _generate_social_calendar_with_llm(...) -> Optional[List[CalendarPostView]]:
    """
    Generate social calendar with robust fallback handling.
    
    PASS 1: Generate calendar skeleton (days + themes)
    PASS 2: Generate captions and CTAs for each day
    PASS 3: (Optional) Humanize individual days
    
    Validation & Fallback:
    - Per-day validation (not whole calendar)
    - If one day weak/unparseable → use template for that day only
    - Calendar ALWAYS returned (no None)
    """
```

---

## Backwards Compatibility Guarantees

✅ **Public API signatures unchanged:**
- `api_aicmo_generate_report(payload)` → same input/output
- `generate_sections(...)` → same function signature
- `SECTION_GENERATORS` dict → still accessible by section_id

✅ **Existing section generators still work:**
- Individual `_gen_*()` functions still callable
- Only their prompts improved (with outline + ranges)
- No behavior change to callers

✅ **Existing tests should pass:**
- Test suite focuses on output existence, not 500 errors
- No 500 errors means more tests pass automatically
- Stub mode still works as before

---

## Testing Strategy

### Phase 1: Unit Tests (Per Layer)
- `test_layer1_raw_draft.py` - Verify raw generation works
- `test_layer2_humanizer.py` - Verify humanizer improves tone
- `test_layer3_soft_validators.py` - Verify scoring & warnings, no exceptions
- `test_layer4_rewriter.py` - Verify rewrites improve quality

### Phase 2: Integration Tests
- `test_4layer_pipeline_end_to_end.py` - Full pack generation
- Verify all sections returned, no 500s, quality improves
- Social calendar always returns, no parsing errors

### Phase 3: Regression Tests
- Run existing test suite
- Verify no breakage to callers (Streamlit, CAM, etc.)
- Confirm all 1029 existing passing tests still pass

### Phase 4: Smoke Tests
- Generate each pack type (Basic, Standard, Premium, Enterprise)
- Verify no 500 errors
- Verify quality scores tracked

---

## Timeline & Order of Implementation

1. **Create new layer modules** (Layer 1–4 files)
2. **Implement Layer 1 wrapper** + adjust prompts in existing generators
3. **Implement Layer 2 humanizer**
4. **Implement Layer 3 soft validators**
5. **Implement Layer 4 rewriter**
6. **Wire into generate_sections()**
7. **Refactor report_enforcer.py** to be soft/non-blocking
8. **Harden social calendar**
9. **Add tests**
10. **Run full test suite**
11. **Verify no regressions**

---

## Success Criteria

✅ **No 500 errors** from quality/benchmark issues  
✅ **All sections returned** for every request  
✅ **Quality improves** via humanizer + rewriter  
✅ **Backward compatible** - existing callers unaffected  
✅ **Tests pass** - 1029+ existing tests still passing  
✅ **Social calendar stable** - never raises, always returns calendar  

---

## Implementation Notes

- Use existing LLM clients (Claude/OpenAI via `_get_llm_provider()`)
- Lazy imports to avoid circular dependencies
- Comprehensive logging for debugging but no stack traces to API
- All exceptions caught and logged, never propagated
- Focus on small, testable functions
- Factor out common patterns (e.g., prompt building, LLM calls)

---

**Next Step:** Begin implementation of Layer 1 wrapper and Layer 2 humanizer.
