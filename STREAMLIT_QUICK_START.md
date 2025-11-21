# 🚀 STREAMLIT QUICK START

## Start the App
```bash
cd /workspaces/AICMO
source .venv-1/bin/activate
streamlit run streamlit_app.py --logger.level=debug
```

## Open Browser
```
http://localhost:8501
```

## What You'll See
1. **Main Dashboard** – Developer testing tools
2. **Sidebar Navigation** – "Pages" dropdown
3. **Click "Operator Dashboard"** – Operator UI loads
4. **Make changes** – Auto-updates (no restart needed)

## File Structure
```
/workspaces/AICMO/
├── streamlit_app.py              (Main page)
├── pages/
│   └── 1_Operator_Dashboard.py   (Operator page)
└── .streamlit/
    └── config.toml               (Config - runOnSave, debug, etc.)
```

## Verify It Works
- ✅ Dashboard loads
- ✅ Sidebar shows "Pages" dropdown
- ✅ Can click "Operator Dashboard"
- ✅ Edit a file, browser auto-updates
- ✅ Debug logs show "✅ [DEBUG] ... loaded from:"

## If Issues
```bash
# Nuclear option - reset everything
./fix_streamlit_cache.sh

# Then restart:
streamlit run streamlit_app.py --logger.level=debug
```

## Documentation
- Full audit: `STREAMLIT_STALE_UI_AUDIT.md`
- Verification: `STREAMLIT_FIX_VERIFICATION.md`
- Summary: `STREAMLIT_STALE_UI_FIX_COMPLETE.md`

---

**Fixed:** Stale UI cache, multipage routing, fresh imports  
**Ready:** Phase 7 UI Integration Test ✅
