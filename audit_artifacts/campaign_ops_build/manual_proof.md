# Campaign Operations - Manual End-to-End Proof Steps

## Prerequisites

- PostgreSQL database running (or SQLite for local)
- Environment: `DATABASE_URL` set
- Python 3.11+
- All AICMO dependencies installed

## Step 1: Apply Database Migration

```bash
cd /workspaces/AICMO

# Verify alembic config
alembic -c alembic.ini current

# Apply migration
alembic -c alembic.ini upgrade head

# Verify tables created
psql $DATABASE_URL -c "\dt campaign_ops_*"
# Expected output: 6 tables created
#   campaign_ops_campaigns
#   campaign_ops_plans
#   campaign_ops_calendar_items
#   campaign_ops_operator_tasks
#   campaign_ops_metric_entries
#   campaign_ops_audit_log
```

**Expected Result**: All 6 campaign_ops tables created in database

---

## Step 2: Start AICMO Infrastructure

```bash
# In separate terminals:

# Terminal 1: Backend API
cd /workspaces/AICMO/backend
python -m uvicorn main:app --reload --port 8000

# Terminal 2: AOL Worker (daemon)
cd /workspaces/AICMO
python scripts/run_aol_worker.py

# Terminal 3: Streamlit UI
cd /workspaces/AICMO
streamlit run streamlit_pages/aicmo_operator.py
```

**Expected Results**:
- Backend running on localhost:8000
- AOL worker ticking (see logs)
- Streamlit UI at localhost:8501
- Campaign Ops tab visible in dashboard

---

## Step 3: Create a Campaign

**In Streamlit UI**:

1. Go to **"Campaign Ops"** tab
2. Select sub-tab **"Campaigns"**
3. Click **"➕ New Campaign"** button
4. Fill form:
   - Campaign Name: `Test Q1 2025 Campaign`
   - Client Name: `Test Client`
   - Venture: `Sales Dev`
   - Objective: `Generate 50 qualified leads in fintech`
   - Platforms: `[linkedin, twitter]` (select both)
   - Start Date: Today
   - End Date: 14 days from today
   - Primary CTA: `Reply with AUDIT`
   - LinkedIn posts/week: `3`
   - Twitter posts/week: `2`
5. Click **"Create Campaign"** button

**Expected Result**:
- ✅ Campaign created message
- Campaign appears in list
- Status: PLANNED

**Database Check**:
```bash
psql $DATABASE_URL -c "SELECT id, name, status FROM campaign_ops_campaigns ORDER BY created_at DESC LIMIT 1;"
# Expected: (1, 'Test Q1 2025 Campaign', 'PLANNED')
```

---

## Step 4: Generate Campaign Plan

**In Streamlit UI**:

1. In Campaign List, click **"View"** on the campaign
2. System navigates to Campaign Detail (or shows plan section)
3. In **"Campaigns"** tab, look for **"Generate Plan"** button
4. Click it
5. Optional: Enter angles, positioning, messaging, themes

**Expected Result**:
- ✅ Plan created message
- Plan appears with version=1

**Database Check**:
```bash
psql $DATABASE_URL -c "SELECT id, campaign_id, generated_by, version FROM campaign_ops_plans ORDER BY created_at DESC LIMIT 1;"
# Expected: (1, 1, 'manual', 1)
```

---

## Step 5: Generate Calendar

**In Streamlit UI**:

1. Go to **"Calendar"** tab
2. Select the campaign
3. Click **"Generate Calendar (14 days)"**

**Expected Result**:
- ✅ Generated N calendar items message
- N = cadence_linkedin * 2 weeks + cadence_twitter * 2 weeks
- For our example: (3*2) + (2*2) = 10 items

**Database Check**:
```bash
psql $DATABASE_URL -c "SELECT id, platform, status, scheduled_at FROM campaign_ops_calendar_items WHERE campaign_id = 1 ORDER BY scheduled_at LIMIT 3;"
# Expected: Multiple rows with platforms linkedin/twitter, status PENDING, future dates
```

---

## Step 6: Generate Tasks from Calendar

**In Streamlit UI**:

1. Go to **"Campaigns"** tab
2. Select campaign, look for **"Generate Tasks from Calendar"** button
3. Click it

**Expected Result**:
- ✅ Generated N operator tasks message
- Each task linked to calendar item

**Database Check**:
```bash
psql $DATABASE_URL -c "SELECT id, platform, task_type, status, due_at FROM campaign_ops_operator_tasks WHERE campaign_id = 1 ORDER BY due_at LIMIT 3;"
# Expected: Tasks with type POST, status PENDING, due dates matching calendar
```

---

## Step 7: View and Complete Today's Tasks

**In Streamlit UI**:

1. Go to **"Today's Tasks"** tab
2. Select campaign

**Expected Result**:
- Tasks due today displayed
- Each task shows:
  - Title
  - Platform
  - Copy text (editable)
  - SOP instructions (expander)
  - Status
  - "Mark Done" button

**Complete a Task**:

1. Click **"Mark Done"** on a task
2. Form appears:
   - Proof type: Select "URL"
   - Proof value: Enter `https://linkedin.com/feed/update/...` (example)
3. Click **"Complete Task"**

**Expected Result**:
- ✅ Task completed message
- Status changes to DONE
- completed_at set to now
- Follow-up ENGAGE tasks auto-created at +2h and +24h

**Database Check**:
```bash
psql $DATABASE_URL -c "SELECT id, status, completion_proof_type, completion_proof_value FROM campaign_ops_operator_tasks WHERE id = (SELECT id FROM campaign_ops_operator_tasks WHERE campaign_id = 1 ORDER BY completed_at DESC LIMIT 1);"
# Expected: status=DONE, proof_type=URL, proof_value=https://...

psql $DATABASE_URL -c "SELECT COUNT(*) FROM campaign_ops_operator_tasks WHERE campaign_id = 1 AND task_type = 'ENGAGE';"
# Expected: 2 (the auto-created follow-up tasks)
```

---

## Step 8: Log Metrics

**In Streamlit UI**:

1. Go to **"Metrics"** tab
2. Select campaign
3. Fill form:
   - Platform: `linkedin`
   - Date: Today
   - Metric: `impressions`
   - Value: `1250`
   - Notes: `Post from 9am blast`
4. Click **"Log Metric"** button

**Expected Result**:
- ✅ Metric logged message
- Metric stored in database

**Repeat** with different metrics:
- platform: `twitter`, metric: `engagement`, value: `45`
- platform: `linkedin`, metric: `clicks`, value: `23`

**Database Check**:
```bash
psql $DATABASE_URL -c "SELECT platform, metric_name, metric_value FROM campaign_ops_metric_entries WHERE campaign_id = 1 ORDER BY created_at;"
# Expected: 3 rows (impressions, engagement, clicks)
```

---

## Step 9: Generate Weekly Summary

**In Streamlit UI**:

1. Go to **"Reports"** tab
2. Select campaign
3. Click **"Generate Weekly Summary"**

**Expected Result**:
- Summary displays with:
  - Week start/end dates
  - Tasks: Planned, Completed, Overdue, Completion %
  - Top Platform
  - Metrics by platform
  - Summary notes

**Example Output**:
```
Weekly Campaign Summary: Test Q1 2025 Campaign
Week: 2025-12-15 to 2025-12-22

Tasks:
- Planned: 10
- Completed: 1
- Completion rate: 10.0%
- Overdue: 0

Top Platform: linkedin

Metrics by Platform:
  linkedin:
    - impressions: 1250.0
    - clicks: 23.0
  twitter:
    - engagement: 45.0

Next Week Focus:
Review performance data above and adjust cadence/messaging as needed.
```

**Database Check**:
```bash
psql $DATABASE_URL -c "SELECT action, entity_type, entity_id FROM campaign_ops_audit_log WHERE action = 'generated_weekly_summary' ORDER BY created_at DESC LIMIT 1;"
# Expected: Row with action=generated_weekly_summary, entity_type=campaign, entity_id=1
```

---

## Step 10: Test Persistence (Restart & Verify)

**Proof that data persists to database**:

1. In Streamlit UI, note current campaign state (e.g., completed tasks, metrics)
2. Stop Streamlit (Ctrl+C)
3. Wait 5 seconds
4. Restart Streamlit:
   ```bash
   streamlit run streamlit_pages/aicmo_operator.py
   ```
5. Navigate to Campaign Ops → Campaigns
6. Open the same campaign

**Expected Result**:
- ✅ All data intact
- Tasks show same completion status
- Metrics still visible
- No data loss

---

## Step 11: Test Audit Log (Accountability)

**In SQL**:

```bash
psql $DATABASE_URL -c "SELECT action, entity_type, entity_id, actor, created_at FROM campaign_ops_audit_log ORDER BY created_at DESC LIMIT 10;"
```

**Expected Output**:
```
action                      | entity_type | entity_id | actor    | created_at
--------------------------|-------------|-----------|----------|------------------
completed_task             | task        | 1         | operator | 2025-12-16 20:30:01
generated_tasks            | campaign    | 1         | operator | 2025-12-16 20:29:00
generated_calendar         | campaign    | 1         | operator | 2025-12-16 20:28:00
generated_plan             | plan        | 1         | operator | 2025-12-16 20:27:00
created_campaign           | campaign    | 1         | operator | 2025-12-16 20:26:00
```

Each action logged with timestamp and actor for accountability.

---

## Step 12: Test AOL Integration (Optional)

**Enqueue a CAMPAIGN_TICK action**:

```bash
python3 << 'EOF'
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ['PYTHONPATH'] = '/workspaces/AICMO'

from aicmo.orchestration.queue import ActionQueue
from aicmo.core.db import get_engine

engine = get_engine()
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# Enqueue CAMPAIGN_TICK action
ActionQueue.enqueue_action(
    session,
    action_type="CAMPAIGN_TICK",
    payload={"campaign_id": 1},
    idempotency_key=f"manual_test_{datetime.utcnow().isoformat()}",
)

print("✅ CAMPAIGN_TICK action enqueued")
session.close()
EOF
```

**In AOL Worker Terminal**:
- Watch for: `[CAMPAIGN_TICK] Updated X tasks` log message
- Indicates action was processed

**Database Check**:
```bash
psql $DATABASE_URL -c "SELECT action_type, status FROM aol_actions ORDER BY created_at DESC LIMIT 1;"
# Expected: action_type=CAMPAIGN_TICK, status=SUCCESS
```

---

## Success Checklist

- [ ] Campaign created (PLANNED status)
- [ ] Plan generated (version 1)
- [ ] Calendar generated (10+ items)
- [ ] Tasks generated from calendar
- [ ] Task completed with proof
- [ ] Follow-up tasks auto-created
- [ ] Metrics logged (3+ entries)
- [ ] Weekly summary generated
- [ ] Data persists after restart
- [ ] Audit log shows all actions
- [ ] (Optional) AOL tick action processed

---

## Troubleshooting

### Issue: "Database connection failed"
- **Check**: `DATABASE_URL` environment variable set
- **Check**: PostgreSQL running and accessible
- **Fix**: `export DATABASE_URL=postgresql://user:pass@host/dbname`

### Issue: "Campaign Ops tab not visible"
- **Check**: `AICMO_CAMPAIGN_OPS_ENABLED=true` (default)
- **Check**: Streamlit reloaded
- **Fix**: Set env and restart Streamlit

### Issue: "ImportError: No module named 'aicmo.campaign_ops'"
- **Check**: Python path includes `/workspaces/AICMO`
- **Check**: `aicmo/campaign_ops/__init__.py` exists
- **Fix**: `export PYTHONPATH=/workspaces/AICMO:$PYTHONPATH`

### Issue: "Alembic migration failed"
- **Check**: Current Alembic revision: `alembic current`
- **Check**: Migration file syntax: `python -m py_compile db/alembic/versions/0001_campaign_ops_*.py`
- **Fix**: Reset DB and re-apply: `alembic downgrade base` then `alembic upgrade head`

---

## Cleanup (Optional)

**Remove test data**:
```bash
psql $DATABASE_URL -c "DELETE FROM campaign_ops_* WHERE campaign_id = 1;"
```

**Downgrade database**:
```bash
alembic -c alembic.ini downgrade fa9783d90970
# Removes campaign_ops tables
```

---

## End-to-End Result

**Operator can now**:
1. ✅ Create campaigns with objectives, platforms, cadence
2. ✅ Generate planning (strategy angles)
3. ✅ Generate calendar (posts per platform per day)
4. ✅ Generate operator tasks with WHERE+HOW instructions
5. ✅ View today/overdue/upcoming tasks
6. ✅ Complete tasks with proof (URL/text/upload)
7. ✅ Auto-create engagement follow-up tasks
8. ✅ Log manual metrics per platform
9. ✅ Generate weekly summaries with KPIs
10. ✅ Full audit trail of all actions
11. ✅ AOL integration for tick/escalation/reporting (optional)

**All safe, all proof-mode (no real posting)**
