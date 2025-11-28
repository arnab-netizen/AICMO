# AICMO Audit Results – Usage Guide

This guide explains how to interpret and act on the comprehensive audit of the AICMO repository.

## Generated Audit Files

### 1. **AICMO_STATUS_AUDIT.md** – Main Report
**What it contains:**
- Complete repository structure map
- Wiring audit (presets vs. generators vs. WOW rules)
- Test coverage analysis
- Critical issues with evidence
- Risk register
- Production readiness assessment

**How to use:**
1. Start with **Executive Summary** at top
2. Read **Section 2: Wiring Audit** – understand the critical generator gap
3. Review **Section 10: What's Implemented vs. Broken**
4. Check **Section 13: Action Items** for priorities

### 2. **AICMO_AUDIT_COMPLETION_SUMMARY.md** – Executive Summary
**What it contains:**
- Test results (28 passing, 6 failing)
- Critical findings with evidence
- Coverage assessment (green/yellow/red areas)
- Production readiness matrix
- Prioritized recommendations

**How to use:**
1. For quick status: Read top section
2. For action items: Go to "Recommendations" section
3. For impact analysis: Check "Production Readiness Matrix"

### 3. **backend/tests/test_aicmo_status_checks.py** – Validation Tests
**What it contains:**
- 34 contract validation tests
- Checks for generator registry, presets, endpoints
- Identifies missing generators and wiring issues
- Validates data integrity

**How to use:**
```bash
# Run all status checks
pytest backend/tests/test_aicmo_status_checks.py -v

# Run specific test class
pytest backend/tests/test_aicmo_status_checks.py::TestSectionGenerators -v

# See which generators are missing
pytest backend/tests/test_aicmo_status_checks.py::TestWiringConsistency -v
```

---

## Key Findings – At a Glance

### 🔴 CRITICAL ISSUES

1. **Quick Social Pack Not Ready**
   - Missing 6 generators (test: `test_quick_social_ready` FAILING)
   - Missing: content_buckets, weekly_social_calendar, creative_direction_light, hashtag_strategy, platform_guidelines, kpi_plan_light
   - **Action:** Implement these 6 generators immediately

2. **31 Total Missing Generators**
   - Presets reference 76 sections, only 45 have implementations
   - **Action:** Audit all missing sections, implement or remove from presets

3. **Competitor Research Endpoint Failing**
   - Tests expect 200, getting 404
   - **Action:** Debug test client route registration

### 🟡 MEDIUM PRIORITY ISSUES

4. **Function Signature Mismatches**
   - API contracts not matching test assumptions
   - **Action:** Update docstrings and tests

5. **Section ID Naming**
   - Some section IDs contain numbers, regex too strict
   - **Action:** Update naming standards

---

## How to Fix Issues

### Issue #1: Add Missing Generators

**File:** `backend/main.py`

**Current:** 45 entries in SECTION_GENERATORS dict (line 1343)

**Action:**
1. Open `backend/main.py`
2. Find SECTION_GENERATORS dict (around line 1343)
3. For each missing section:
   - Write generator function `_gen_section_name()`
   - Add entry to dict: `"section_name": _gen_section_name,`
4. Test: Run status checks to verify

**Example:**
```python
def _gen_content_buckets(req: GenerateRequest, **kwargs) -> str:
    """Generate content buckets section."""
    # Implementation
    return sanitize_output(raw, req.brief)

SECTION_GENERATORS = {
    # ... existing entries ...
    "content_buckets": _gen_content_buckets,  # ADD THIS LINE
    # ... more entries ...
}
```

### Issue #2: Fix Competitor Research Endpoint

**File:** `backend/tests/conftest.py` or test client setup

**Problem:** Tests get 404 on `/api/competitor/research`

**Action:**
1. Check if endpoint is registered in test app factory
2. Verify route is in conftest.py's app setup
3. Debug test client to ensure all routes are mounted
4. Re-run tests to verify 200 response

**Test:** Run `pytest backend/tests/test_competitor_research_endpoint.py -v`

### Issue #3: Implement Remaining Generators

**Priority order (highest value first):**
1. `ad_concepts` – Used in 5+ packs
2. `market_landscape` – Used in 4+ packs
3. `brand_audit` – Used in 3+ packs
4. `email_automation_flows` – Core feature
5. `landing_page_blueprint` – Premium tier
6. ... then remaining 26 generators

**Process:**
1. For each generator, find references in presets
2. Understand what it should do (check docstrings, comments)
3. Implement function in `backend/main.py`
4. Add to SECTION_GENERATORS dict
5. Run status checks to verify

---

## Testing Your Fixes

### After implementing a generator:

```bash
# Verify it's in the registry
python -c "from backend.main import SECTION_GENERATORS; print('section_name' in SECTION_GENERATORS)"

# Run status checks to see improved pass rate
pytest backend/tests/test_aicmo_status_checks.py -v

# Run pack E2E tests to ensure packs still work
pytest backend/tests/test_pack_reports_e2e.py -v
```

### After fixing tests:

```bash
# Run competitor research tests
pytest backend/tests/test_competitor_research_endpoint.py -v

# Run full test suite to ensure no regressions
pytest --tb=short -q
```

---

## Monitoring Progress

### Track improvements with status checks:

```bash
# Generate before/after comparison
pytest backend/tests/test_aicmo_status_checks.py -v > before.txt
# ... make changes ...
pytest backend/tests/test_aicmo_status_checks.py -v > after.txt
# Compare
diff before.txt after.txt
```

### Expected progression:
- **Day 1:** Fix Quick Social (6 generators) → 28→32 tests passing
- **Day 2:** Fix competitor endpoint → 32→33 tests passing  
- **Day 3-5:** Implement remaining generators incrementally
- **Target:** 34/34 tests passing + all pack E2E tests green

---

## Validation Checklist

### Before marking "DONE":

- [ ] All status checks passing (34/34)
- [ ] Quick Social pack E2E test passing
- [ ] Standard Campaign pack E2E test passing
- [ ] Competitor research endpoint returning 200
- [ ] No test regressions in full test suite
- [ ] At least 2 advanced packs (Premium/Enterprise) working
- [ ] Learning system tests still passing
- [ ] Export tests (PDF/PPTX/ZIP) still passing

### Production readiness:
- [ ] All basic packs (Quick Social, Standard) 100% working
- [ ] At least 1 advanced pack (Premium) working
- [ ] Learning system fully functional
- [ ] Exports all modes working
- [ ] No known data loss scenarios
- [ ] Error handling comprehensive

---

## References

### Key Files to Understand

1. **Generator Registry:** `backend/main.py` (lines 1343-1390)
2. **Presets:** `aicmo/presets/package_presets.py`
3. **WOW Rules:** `aicmo/presets/wow_rules.py`
4. **Pack Generation:** `backend/main.py` (function `generate_sections()`)
5. **Tests:** `backend/tests/test_aicmo_status_checks.py`

### Related Documentation

- AICMO_STATUS_AUDIT.md – Comprehensive technical audit
- ROUTE_VERIFICATION_CONFIRMED.md – Endpoint verification
- IMPLEMENTATION_HANDOFF.md – Previous session notes

### Commands Reference

```bash
# Run status checks
pytest backend/tests/test_aicmo_status_checks.py -v -W ignore::DeprecationWarning

# Run specific test
pytest backend/tests/test_aicmo_status_checks.py::TestWiringConsistency::test_quick_social_sections_in_generators -v

# List all failing tests
pytest backend/tests/test_aicmo_status_checks.py --tb=no -q

# Run with detailed output
pytest backend/tests/test_aicmo_status_checks.py -vv --tb=short

# Generate audit script output
python audit_script.py
```

---

**Next Step:** Review AICMO_STATUS_AUDIT.md Section 13 "Summary & Recommendations" for detailed action plan.

