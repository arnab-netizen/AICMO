# OPERATOR_V2 - Quick Reference

**Build**: `OPERATOR_V2_2025_12_16`  
**Status**: ✅ PRODUCTION READY

---

## Quick Start

```bash
# Verify locally
python -m py_compile operator_v2.py aicmo/ui_v2/*.py aicmo/ui_v2/tabs/*.py
python scripts/test_operator_v2_smoke.py

# Run Streamlit
python -m streamlit run operator_v2.py

# Deploy Docker
docker build -f streamlit/Dockerfile -t aicmo:v2 .
docker run -p 8501:8501 aicmo:v2
```

---

## What's New

✅ **11 Modular Tabs** - Each independent, no cascade failures  
✅ **Safe DB Wrapping** - `safe_session()` context manager (Fix C1)  
✅ **Safe Enum Handling** - Removed invalid ENGAGED status (Fix C2)  
✅ **DB Diagnostics** - Comprehensive checks + remediation (Fix C3)  
✅ **Backend HTTP** - Prefer backend over direct DB (Requirement D)  
✅ **Campaign Workflow** - Create → Generate → Approve → Execute (Requirement E)  
✅ **Manual Posting** - Copy-paste platform instructions (Agency-operable)  
✅ **Watermark** - Visible proof of entrypoint: `DASHBOARD_BUILD=OPERATOR_V2_2025_12_16`

---

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `operator_v2.py` | 131 | Main entrypoint + watermark |
| `aicmo/ui_v2/shared.py` | 365 | DB + HTTP + diagnostics helpers |
| `aicmo/ui_v2/router.py` | 85 | Tab router (11 tabs) |
| `aicmo/ui_v2/tabs/*.py` | 1,100 | 11 tab modules |
| `scripts/test_operator_v2_smoke.py` | 160 | Smoke test script |
| **DOCUMENTATION** | 550+ | Implementation guide |

**Total**: ~2,100 lines of production code

---

## Files Modified

| File | Change |
|------|--------|
| `streamlit/Dockerfile` | CMD: `operator_v2.py` (was `streamlit_pages/aicmo_operator.py`) |
| `scripts/launch_operator_ui.sh` | Updated to run `operator_v2.py` |

---

## Files Preserved (Rollback)

- ✅ `streamlit_pages/aicmo_operator.py` - Still exists (116 KB)
- ✅ All backend code - Unchanged
- ✅ All database models - Unchanged

---

## The 11 Tabs

1. **📥 Intake** - Lead intake forms
2. **📊 Strategy** - Campaign planning
3. **🎨 Creatives** - Content assets
4. **🚀 Execution** - Post scheduling + platform guides
5. **📈 Monitoring** - Analytics & metrics
6. **🎯 Lead Gen** - Lead scoring (safe enums)
7. **🎬 Campaigns** - 4-step operator workflow
8. **🤖 Autonomy** - AI agent settings
9. **📦 Delivery** - Reports & exports
10. **📚 Learn** - Knowledge base
11. **🔧 System** - Diagnostics panel

---

## Verification

### Smoke Test (All Pass ✅)
```
✅ Import operator_v2
✅ Import 11 tabs
✅ Import router (11 tabs registered)
✅ Watermark visible: OPERATOR_V2_2025_12_16
✅ All helpers callable (DB + HTTP)
✅ No compilation errors
```

### Entrypoint Proof
- Dockerfile uses `operator_v2.py`
- Watermark visible on startup: `[DASHBOARD] DASHBOARD_BUILD=OPERATOR_V2_2025_12_16`
- If you see this, entrypoint is V2

### Runtime Errors Fixed
- ✅ C1: No more `_GeneratorContextManager.execute()` errors
- ✅ C2: No more invalid LeadStatus.ENGAGED enum crashes
- ✅ C3: Comprehensive DB diagnostics now available

---

## Key Improvements

| Issue | Before | After |
|-------|--------|-------|
| **DB Sessions** | Direct use, might crash | Context manager safe |
| **Enum Errors** | Invalid ENGAGED fails | Only valid values |
| **DB Diagnostics** | None | Full config + connectivity check |
| **Backend HTTP** | N/A | Native support in all tabs |
| **Campaign Flow** | N/A | Create → Generate → Approve → Execute |
| **Manual Posting** | N/A | Platform-specific instructions |
| **Tab Errors** | Cascade fail | Isolated, graceful fallback |
| **Watermark** | N/A | Always visible: OPERATOR_V2_2025_12_16 |

---

## Deployment Checklist

- [ ] Run smoke test locally
- [ ] Verify compilation (0 errors)
- [ ] Build Docker image
- [ ] Run container, check logs for watermark
- [ ] Verify all 11 tabs load
- [ ] Click each tab, verify no crashes
- [ ] Check System/Diagnostics for env warnings
- [ ] Monitor first day of production

---

## Rollback Procedure

If critical issues:
1. Edit `streamlit/Dockerfile` - change `operator_v2.py` back to `streamlit_pages/aicmo_operator.py`
2. Edit `scripts/launch_operator_ui.sh` - change `operator_v2.py` back to `streamlit_pages/aicmo_operator.py`
3. Rebuild and deploy
4. Old dashboard live immediately (operator.py still exists)

---

## Support & Next Steps

- **Documentation**: See `OPERATOR_V2_IMPLEMENTATION_COMPLETE.md` (550+ lines)
- **Test Script**: `scripts/test_operator_v2_smoke.py`
- **Code**: All modules in `aicmo/ui_v2/` and `operator_v2.py`

**Questions? Check System/Diagnostics tab for environment status.**
