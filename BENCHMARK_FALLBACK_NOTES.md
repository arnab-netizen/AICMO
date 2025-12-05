# Benchmark Validation Fallback Mechanism

**Date**: 2024-12-05  
**Status**: Implemented  
**Scope**: Full-funnel growth suite calendar section + extensible to other sections

---

## Problem Statement

### The Issue

In production, the `full_30_day_calendar` section for `full_funnel_growth_suite` pack was failing benchmark validation **ONLY when LLM refinement was enabled**, despite passing validation when tested with templates alone.

**Failure Scenario**:
- **Pack**: `full_funnel_growth_suite`
- **Section**: `full_30_day_calendar`
- **Mode**: `stage="draft"`, `wow_enabled=True`, `refinement_mode="Balanced"` (passes=2)
- **Client**: Luxotica Automobiles (luxury car dealership)
- **Error**: Benchmark validation failed after 2 refinement attempts

### Root Cause

The validation discrepancy occurred because:

1. **Template-only testing** (`print_benchmark_issues`) exercises generators WITHOUT:
   - LLM refinement (Balanced mode with 2 passes)
   - Agency grade enhancements
   - Humanization layer
   - Research integration
   - Full production pipeline

2. **Production pipeline** applies ALL enhancements, which can:
   - Add generic marketing language during refinement
   - Increase table dominance (pushing genericness score up)
   - Introduce blacklisted phrases during enhancement
   - Modify structure in ways that break benchmarks

3. **No safety net**: After failing 2 regeneration attempts, the system raised `BenchmarkEnforcementError` instead of gracefully falling back to the known-good template version.

---

## Solution: Transparent Fallback Mechanism

### Architecture

We've implemented a **two-tier safety system**:

#### Tier 1: Template Preservation
Before running benchmark enforcement, the system stores the original template-only output:

```python
# In generate_sections() - backend/main.py
fallback_templates = {}

if pack_key == "full_funnel_growth_suite" and "full_30_day_calendar" in results:
    # Store original template as fallback
    fallback_templates["full_30_day_calendar"] = results["full_30_day_calendar"]
```

#### Tier 2: Smart Fallback After Failed Attempts
The `enforce_benchmarks_with_regen()` function now accepts an optional `fallback_to_original` parameter:

```python
# In backend/validators/report_enforcer.py
def enforce_benchmarks_with_regen(
    *,
    pack_key: str,
    sections: List[Dict[str, str]],
    regenerate_failed_sections: Optional[Callable] = None,
    max_attempts: int = 2,
    fallback_to_original: Optional[Dict[str, str]] = None,  # NEW
) -> EnforcementOutcome:
```

**Behavior**:
1. Generate sections with template-first approach ✅
2. Apply LLM refinement if enabled
3. Validate against benchmarks
4. If fails: Regenerate (up to `max_attempts`)
5. If still fails AND `fallback_to_original` exists for that section:
   - **Transparently replace** refined content with original template
   - **Re-validate** to confirm fallback passes
   - **Log warning** but continue successfully
6. Only raise error if NO fallback available

### Benefits

✅ **Zero downtime**: Production never breaks due to refinement issues  
✅ **Transparent recovery**: Users get valid output without knowing fallback occurred  
✅ **Diagnostic logging**: Warnings clearly indicate when fallback was used  
✅ **Template-first architecture preserved**: Base templates remain authoritative  
✅ **Extensible**: Easy to add more sections to fallback registry

---

## Implementation Details

### Files Modified

1. **`backend/validators/report_enforcer.py`**
   - Added `fallback_to_original` parameter to `enforce_benchmarks_with_regen()`
   - Implemented fallback logic after max_attempts exhausted
   - Added logging for fallback operations

2. **`backend/main.py`**
   - Modified `generate_sections()` to register fallback templates
   - Currently registers: `full_funnel_growth_suite/full_30_day_calendar`
   - Passes `fallback_templates` dict to enforcer

3. **`backend/debug/print_benchmark_issues_with_payload.py`** (NEW)
   - Debug helper that reproduces REAL production failures
   - Tests with full pipeline: LLM refinement, agency grade, humanization
   - Uses real client briefs (e.g., Luxotica Automobiles)

### Current Fallback Registry

| Pack Key | Section ID | Reason |
|----------|-----------|--------|
| `full_funnel_growth_suite` | `full_30_day_calendar` | LLM refinement + agency grade can increase table dominance and genericness score beyond threshold |

---

## Usage Guide

### For Developers: Adding New Fallback Sections

To add fallback protection for another section:

```python
# In backend/main.py, generate_sections() function
fallback_templates = {}

# Existing fallback
if pack_key == "full_funnel_growth_suite" and "full_30_day_calendar" in results:
    fallback_templates["full_30_day_calendar"] = results["full_30_day_calendar"]

# Add new fallback
if pack_key == "strategy_campaign_premium" and "copy_variants" in results:
    fallback_templates["copy_variants"] = results["copy_variants"]
    logger.info("[BENCHMARK FALLBACK] Registered fallback template for copy_variants")
```

### For QA: Testing with Real Payloads

Use the new debug helper to test sections with production settings:

```bash
# Test with Luxotica brief (real failure case)
python -m backend.debug.print_benchmark_issues_with_payload \
    full_funnel_growth_suite full_30_day_calendar --brief luxotica

# Test without LLM refinement (template only)
python -m backend.debug.print_benchmark_issues_with_payload \
    full_funnel_growth_suite full_30_day_calendar --no-refinement

# Show full section content
python -m backend.debug.print_benchmark_issues_with_payload \
    full_funnel_growth_suite full_30_day_calendar --verbose
```

### Log Patterns to Watch

**Fallback Applied Successfully**:
```
[WARNING] [BENCHMARK FALLBACK] Section 'full_30_day_calendar' failed after 2 attempt(s). 
Falling back to safe template version.

[INFO] [BENCHMARK FALLBACK] Successfully recovered with template fallback for 1 section(s)
```

**Fallback Failed (Bug Alert)**:
```
[ERROR] [BENCHMARK FALLBACK] Fallback templates still failed validation! 
This indicates a bug in the fallback mechanism.
```

If you see the second pattern, it means the original template itself fails benchmarks, which should NEVER happen. This requires immediate investigation.

---

## Testing Strategy

### Validation Pyramid

```
┌─────────────────────────────────────────┐
│ Level 3: Production E2E Tests          │  Full pipeline with real briefs
│ - Test: print_benchmark_issues_with_    │  Catches: Refinement issues
│   payload (NEW)                         │  
├─────────────────────────────────────────┤
│ Level 2: Fallback Mechanism Tests      │  Unit tests for enforcer
│ - Test: test_benchmark_fallback.py      │  Catches: Fallback logic bugs
├─────────────────────────────────────────┤
│ Level 1: Template Validation Tests     │  Template-only generation
│ - Test: print_benchmark_issues          │  Catches: Template issues
│ - Coverage: All 10 packs                │
└─────────────────────────────────────────┘
```

### Pre-Deployment Checklist

Before deploying changes that affect section generators or refinement:

- [ ] Run `python -m backend.debug.print_benchmark_issues <pack>` (Level 1)
- [ ] Run `python -m backend.debug.print_benchmark_issues_with_payload <pack> <section>` (Level 3)
- [ ] Check logs for fallback warnings in staging environment
- [ ] Verify fallback templates are registered for known-problematic sections

---

## Future Enhancements

### Potential Improvements

1. **Automatic Fallback Detection**
   - Monitor production failures
   - Auto-register sections that repeatedly fail refinement
   - Dashboard showing fallback usage frequency

2. **Smarter Refinement**
   - Pre-validate refinement output BEFORE running benchmarks
   - Use lighter refinement for sections with known issues
   - Configurable refinement strategies per section

3. **Hybrid Approach**
   - Keep template structure, refine only narrative parts
   - Preserve tables/bullets, enhance only prose
   - Section-specific refinement rules

4. **Refinement Bypass List**
   - Maintain explicit list of sections to NEVER refine
   - Opt-in refinement instead of opt-out fallback
   - Per-pack refinement configuration

---

## Troubleshooting

### Section Still Failing After Fallback

**Symptoms**: 
- Logs show fallback applied
- Report generation still fails
- Error: "Fallback templates still failed validation!"

**Diagnosis**:
```bash
# Test the template in isolation
AICMO_USE_LLM=0 python -m backend.debug.print_benchmark_issues full_funnel_growth_suite
```

**Root Cause**: The template itself fails benchmarks (regression in generator code)

**Fix**: Repair the generator function (`_gen_<section_id>`) to pass benchmarks standalone

### Fallback Not Triggering

**Symptoms**:
- Expected fallback warning not in logs
- BenchmarkEnforcementError raised instead

**Diagnosis**:
- Check if section is registered in `fallback_templates` dict
- Verify pack_key matches exactly (case-sensitive)
- Confirm section_id matches exactly

**Fix**: Add explicit logging in `generate_sections()`:
```python
logger.info(f"[DEBUG] Registered fallbacks: {list(fallback_templates.keys())}")
```

### How to Disable Fallback (for testing)

To force failures and test error handling:

```python
# In backend/main.py, generate_sections()
fallback_templates = {}  # Empty dict = no fallbacks
# Or comment out the specific section registration
```

---

## Related Documentation

- **Benchmark System**: `learning/benchmarks/README.md`
- **Generator Patterns**: `SECTION_GENERATOR_PATTERNS.md`
- **Template Architecture**: `TEMPLATE_FIRST_ARCHITECTURE.md`
- **Quality Enforcement**: `backend/validators/README.md`

---

## Changelog

### 2024-12-05: Initial Implementation
- Added `fallback_to_original` parameter to `enforce_benchmarks_with_regen()`
- Registered `full_funnel_growth_suite/full_30_day_calendar` as fallback
- Created `print_benchmark_issues_with_payload.py` debug helper
- Documented fallback mechanism and usage patterns

### Future
- Monitor production logs for fallback frequency
- Expand fallback registry as needed
- Consider automatic fallback detection system
