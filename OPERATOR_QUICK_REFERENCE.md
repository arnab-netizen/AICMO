# AICMO Dashboard: Quick Reference for Operators

## 🚀 Launch Dashboard

### Option 1: Direct Streamlit Launch (Most Direct)
```bash
streamlit run streamlit_pages/aicmo_operator.py
```
Dashboard opens at: `http://localhost:8501`

### Option 2: Shell Script (Recommended for CI/CD)
```bash
./scripts/launch_operator_ui.sh
```

### Option 3: Docker (Production)
```bash
docker build -f streamlit/Dockerfile -t aicmo:dashboard .
docker run -p 8501:8501 aicmo:dashboard
```
Dashboard at: `http://localhost:8501`

---

## ✅ Verify You're Running Correct Dashboard

**Open the Diagnostics panel** (bottom of left sidebar) and confirm:

| Item | Expected Value |
|------|---|
| **Build Marker** | `AICMO_DASH_V2_2025_12_16` |
| **Running File** | `streamlit_pages/aicmo_operator.py` |
| **Campaign Ops** | ✅ Importable (or ❌ Not available) |

If any of these shows wrong value or is missing → you're running the wrong dashboard.

---

## 📊 Dashboard Tabs (What You'll See)

1. **Command Center** - Operational commands and system controls
2. **Autonomy** - AI autonomy configuration and behavior
3. **Campaign Ops** - Campaign operational metrics ⚠️ Always visible
4. **Campaigns** - Campaign details (read-only view)
5. **Acquisition** - Lead acquisition dashboard
6. **Strategy** - Strategic planning dashboard
7. **Creatives** - Creative asset management
8. **Publishing** - Publishing pipeline status
9. **Monitoring** - System health and performance
10. **Diagnostics** - Build info and system state

---

## ⚠️ What If Something Goes Wrong?

### "❌ Campaign Ops module not available"
- **Cause**: campaign_ops module not installed or has import error
- **Action**: This is fine! Tab shows disabled state. Check other tabs.
- **Recovery**: `pip install -r requirements.txt` and restart

### Dashboard doesn't start
- **Check**: Are you running correct file?
  ```bash
  ps aux | grep streamlit
  ```
  Should show: `streamlit_pages/aicmo_operator.py`
  
- **If running old file** (app.py, etc.): Kill it and use correct file
  ```bash
  streamlit run streamlit_pages/aicmo_operator.py
  ```

### One tab shows error while others work
- **This is expected!** Each tab has independent error handling
- **What to do**: Check other tabs - they work fine
- **Recovery**: Restart dashboard or fix the erroring tab's module

### "⚠️ MOCK DATA MODE" banner at top
- **Meaning**: Dashboard is using test data, not real data
- **Action**: Check with team if this is intentional
- **Indicators**: Small `[MOCK]` badges on metrics

---

## 🔧 Troubleshooting Quick Links

```bash
# See what file is actually running
ps aux | grep streamlit | grep -v grep

# Check BUILD_MARKER (confirms version)
grep "BUILD_MARKER" streamlit_pages/aicmo_operator.py

# Verify all imports OK
python -c "from streamlit_pages.aicmo_operator import BUILD_MARKER; print(f'✅ OK - {BUILD_MARKER}')"

# See recent errors in dashboard
tail -f ~/.streamlit/logs/*

# Kill and restart
pkill -f "streamlit run"
streamlit run streamlit_pages/aicmo_operator.py
```

---

## 📋 Operational Checklist

**Daily**:
- [✅] Dashboard starts within 3 seconds
- [✅] All 10 tabs visible
- [✅] Campaign Ops tab shows (data or "not available" message)
- [✅] Diagnostics panel accessible

**Weekly**:
- [✅] BUILD_MARKER matches deployed version
- [✅] No persistent errors in any tab
- [✅] Command Center commands responsive

**On Deploy**:
- [✅] Confirm BUILD_MARKER = `AICMO_DASH_V2_2025_12_16`
- [✅] Confirm file path = `streamlit_pages/aicmo_operator.py`
- [✅] Confirm Campaign Ops tab visible
- [✅] Run: `python -c "from streamlit_pages.aicmo_operator import BUILD_MARKER"`

---

## ⛔ Files That Should NOT Be Run

**Do NOT use these files** - they are guarded and will show error:
- ❌ `app.py` (deprecated, shows RuntimeError)
- ❌ `launch_operator.py` (deprecated, exits)
- ❌ `streamlit_app.py` (legacy, st.stop())
- ❌ `streamlit_pages/aicmo_ops_shell.py` (old dashboard)
- ❌ `streamlit_pages/cam_engine_ui.py` (old dashboard)
- ❌ `streamlit_pages/operator_qc.py` (old dashboard)

**Always use**: `streamlit run streamlit_pages/aicmo_operator.py`

---

## 📞 Support

If dashboard doesn't behave as expected:

1. **First**: Check Diagnostics panel for BUILD_MARKER and file path
2. **Then**: Verify you're on right file
3. **Finally**: Check if error is in specific tab (other tabs will work)

---

**Version**: AICMO_DASH_V2_2025_12_16  
**Last Updated**: 2025-12-16  
**Production Ready**: YES ✅
