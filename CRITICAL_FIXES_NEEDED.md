# ⚡ CRITICAL ACTIONS - Integration Fixes Required

## Status: 🔴 BLOCKERS FOUND

All new components exist but are **NOT WIRED** into production endpoints.

---

## 🚨 Top 4 Critical Issues

### Issue #1: Output Validator Never Called
**Impact:** No validation occurs before export  
**Fix Time:** 10 minutes  
**Severity:** 🔴 CRITICAL

```python
# File: backend/main.py, line ~1967
# After: base_output = _apply_wow_to_output(base_output, req)

from backend.validators import OutputValidator
validator = OutputValidator(base_output, req.brief, req.wow_package_key if req.wow_enabled else None)
issues = validator.validate_all()
error_count = sum(1 for i in issues if i.severity == "error")
if error_count > 0:
    logger.warning(f"Validation errors: {validator.get_error_summary()}")
```

---

### Issue #2: Industry Config Never Used
**Impact:** All reports use generic personas/channels  
**Fix Time:** 40 minutes (2 locations)  
**Severity:** 🔴 CRITICAL

**Location A: Personas (line ~1450)**
```python
from backend.industry_config import get_default_personas_for_industry
industry_personas = get_default_personas_for_industry(req.brief.brand.industry)
if industry_personas:
    persona_cards = [PersonaCard(...) for p in industry_personas]
```

**Location B: Channels (line ~1480)**
```python
from backend.industry_config import get_industry_config
config = get_industry_config(req.brief.brand.industry)
if config:
    channels = config.get("channels", {})
    # Use channels in generation logic
```

---

### Issue #3: Pack Scoping Whitelist Not Applied
**Impact:** Basic packs can contain Premium sections  
**Fix Time:** 5 minutes  
**Severity:** 🔴 CRITICAL

```python
# File: backend/main.py, line ~1755
# In extra_sections generation, BEFORE generate_sections() call:

if req.wow_enabled and req.wow_package_key:
    allowed = get_allowed_sections_for_pack(req.wow_package_key)
    if allowed:
        section_ids = [s for s in section_ids if s in allowed]
```

---

### Issue #4: Test Discovery Broken
**Impact:** New tests don't run in CI/CD  
**Fix Time:** 1 minute  
**Severity:** 🟡 MEDIUM

```ini
# File: pytest.ini, line 2
# Change: testpaths = backend/tests
# To:     testpaths = tests backend/tests
```

---

## ✅ What's Already Working

- ✅ PDF template resolver (in use)
- ✅ All 30+ tests written
- ✅ All validation logic implemented
- ✅ All industry configs defined
- ✅ All templates created

---

## 📋 Implementation Checklist

- [ ] **Issue #1 (10 min)** - Wire OutputValidator to /aicmo/generate
- [ ] **Issue #2A (20 min)** - Wire industry config to persona generation
- [ ] **Issue #2B (20 min)** - Wire industry config to channel generation
- [ ] **Issue #3 (5 min)** - Apply pack scoping whitelist
- [ ] **Issue #4 (1 min)** - Fix pytest.ini
- [ ] **Test (5 min)** - Run: `pytest tests/ -v`
- [ ] **Manual (10 min)** - Test all 7 packs, verify correct sections/personas
- [ ] **Deploy** - Push to production

**Total Time: ~1.5 hours to full integration**

---

## 🔗 References

- Full audit details: `IMPLEMENTATION_AUDIT_REPORT.md`
- Validator code: `backend/validators/output_validator.py`
- Industry config: `backend/industry_config.py`
- Pack whitelist: `backend/main.py` lines 118-270
- PDF templates: `backend/templates/pdf/*.html`

---

## Next Step

👉 **Read:** `IMPLEMENTATION_AUDIT_REPORT.md` (sections 1-7)  
👉 **Implement:** Fixes in order 1→2→3→4  
👉 **Test:** Run full test suite  
👉 **Deploy:** To production

