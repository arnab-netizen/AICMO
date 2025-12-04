# Quick Social Pack Protection - Quick Reference

## ⚡ Quick Commands

### Verify Protection is Intact
```bash
python tests/test_quick_social_pack_freeze.py
```

### Run All Validation Tests
```bash
python test_hashtag_validation.py && \
python scripts/dev_validate_benchmark_proof.py && \
python tests/test_quick_social_pack_freeze.py
```

### Create Snapshot Before Changes
```bash
python -c "from backend.utils.non_regression_snapshot import create_snapshot; create_snapshot('snapshots/before.json')"
```

### Compare Snapshots After Changes
```bash
python -c "from backend.utils.non_regression_snapshot import create_snapshot; create_snapshot('snapshots/after.json')"
python -c "from backend.utils.non_regression_snapshot import compare_snapshots; compare_snapshots('snapshots/before.json', 'snapshots/after.json')"
```

---

## 🛡️ What's Protected

### 8 Generator Functions (backend/main.py)
- `_gen_overview` (line ~530)
- `_gen_messaging_framework` (line ~694)
- `_gen_quick_social_30_day_calendar` (line ~1196)
- `_gen_content_buckets` (line ~3577)
- `_gen_hashtag_strategy` (line ~3695)
- `_gen_kpi_plan_light` (line ~3931)
- `_gen_execution_roadmap` (line ~1703)
- `_gen_final_summary` (line ~1899)

### WOW Template (aicmo/presets/wow_templates.py)
- `quick_social_basic` template (line ~14)

---

## ⚠️ Warning Signs

If you see these in source code, **STOP and run tests**:

```python
⚠️  PRODUCTION-VERIFIED: Quick Social Pack (Basic)
DO NOT MODIFY without running: ...
```

```html
<!-- ⚠️ PRODUCTION-VERIFIED TEMPLATE: Quick Social Pack (Basic) -->
<!-- DO NOT change section order, names, or placeholders without updating: ... -->
```

---

## ✅ Required Tests

Before committing changes to Quick Social Pack:

1. **Protection Test**: `python tests/test_quick_social_pack_freeze.py`
2. **Hashtag Test**: `python test_hashtag_validation.py`
3. **Benchmark Test**: `python scripts/dev_validate_benchmark_proof.py`

**All must pass with ✅**

---

## 📁 Protection Files

- **tests/test_quick_social_pack_freeze.py** - Protection verification
- **backend/utils/non_regression_snapshot.py** - Snapshot tool
- **QUICK_SOCIAL_PACK_PROTECTION_COMPLETE.md** - Full documentation
- **QUICK_SOCIAL_PACK_QUICK_REFERENCE.md** - This file

---

## 🚨 Emergency: Protection Test Fails

If `python tests/test_quick_social_pack_freeze.py` fails:

1. **Check Error Message** - Which protection is missing?
2. **Verify Protection Headers** - Are docstrings intact in backend/main.py?
3. **Check WOW Template** - Are HTML comments present?
4. **Review Recent Changes** - Did someone remove safeguards?
5. **Restore from Git** - Revert if safeguards were accidentally removed

---

## 📊 Expected Test Output

### Protection Test
```
✅ PASS: Generator protection headers
✅ PASS: WOW template protection
✅ PASS: Documentation files
✅ PASS: Snapshot utility
RESULTS: 4 passed, 0 failed
```

### Hashtag Test
```
✅ SUCCESS: hashtag_strategy PASSES all quality checks!
```

### Benchmark Test
```
✅ Markdown Parser Works
✅ Quality Checks Work
✅ ALL TESTS PASSED
```

---

## 🎯 Quick Checklist

Before modifying Quick Social generators:

- [ ] Read protection header in function docstring
- [ ] Create baseline snapshot
- [ ] Make changes
- [ ] Run all 3 validation tests
- [ ] Compare snapshots
- [ ] Verify no unintended changes
- [ ] Commit with confidence

---

**Last Updated**: 2025-12-03  
**Status**: ✅ All protections active and verified
