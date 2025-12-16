# Campaign Operations - Quick Reference Card

## 🚀 Quick Start

### 1. Initialize Database
```bash
cd /workspaces/AICMO
alembic upgrade head
```

### 2. Import and Use
```python
from aicmo.campaign_ops.service import CampaignOpsService
from aicmo.database import get_session

session = get_session()
service = CampaignOpsService(session)

# Create campaign
campaign = service.create_campaign("My Campaign", "Description")

# Generate plan
plan = service.generate_plan(campaign.id, "Focus area", 30)

# Get today's tasks
tasks = service.get_today_tasks(campaign.id)
```

### 3. Validate Setup
```bash
python /workspaces/AICMO/audit_artifacts/campaign_ops_build/validation_script.py
```

---

## 📊 Core Models

### Campaign
- **Table:** `campaign_ops_campaigns`
- **Fields:** name, description, status, metadata, timestamps
- **Statuses:** active, paused, completed

### CampaignPlan
- **Table:** `campaign_ops_plans`
- **Links to:** Campaign (1:N)
- **Fields:** phase_number, focus_area, duration_days, tactics, metrics

### CalendarItem
- **Table:** `campaign_ops_calendar_items`
- **Links to:** CampaignPlan (1:N)
- **Fields:** date, content_type, platform_requirements, posting_time

### OperatorTask
- **Table:** `campaign_ops_operator_tasks`
- **Links to:** CalendarItem (1:N)
- **Fields:** platform, task_type, description, status, due_date
- **Platforms:** linkedin, instagram, twitter, email
- **Task Types:** write, review, schedule, post

### MetricEntry
- **Table:** `campaign_ops_metric_entries`
- **Links to:** OperatorTask (1:N)
- **Fields:** metric_type, value, unit, recorded_at

### OperatorAuditLog
- **Table:** `campaign_ops_audit_log`
- **Links to:** Campaign (1:N)
- **Fields:** operator_id, action, details, timestamp

---

## 🎯 Service Methods

| Method | Parameters | Returns |
|--------|-----------|---------|
| `create_campaign()` | name, description, status, metadata | Campaign |
| `get_campaign()` | campaign_id | Campaign |
| `list_campaigns()` | status, limit, offset | List[Campaign] |
| `generate_plan()` | campaign_id, focus_area, duration_days | CampaignPlan |
| `generate_calendar()` | plan_id, content_theme | List[CalendarItem] |
| `generate_tasks_from_calendar()` | calendar_items, assign_to | List[OperatorTask] |
| `get_today_tasks()` | campaign_id | List[OperatorTask] |
| `get_overdue_tasks()` | campaign_id | List[OperatorTask] |
| `mark_task_complete()` | task_id, outcome, metrics | OperatorTask |
| `generate_weekly_summary()` | campaign_id | Dict |
| `get_campaign_metrics()` | campaign_id | Dict |
| `get_task_completion_rate()` | campaign_id | float |

---

## 🔧 Platform SOPs

```python
from aicmo.campaign_ops.instructions import get_platform_sop, list_available_platforms

# List all platforms
platforms = list_available_platforms()
# Output: ['linkedin', 'instagram', 'twitter', 'email']

# Get SOP for specific platform and task
sop = get_platform_sop(platform="linkedin", task_type="post")
```

**Available Platforms:**
- **LinkedIn:** Professional, timing-aware, tag-optimized
- **Instagram:** Visual-focused, hashtag strategy
- **Twitter:** Character-efficient, thread optimization
- **Email:** Personalized, CTA-optimized

---

## 📁 File Locations

| File | Purpose |
|------|---------|
| `aicmo/campaign_ops/__init__.py` | Package initialization |
| `aicmo/campaign_ops/models.py` | Database models |
| `aicmo/campaign_ops/schemas.py` | Pydantic schemas |
| `aicmo/campaign_ops/repo.py` | Repository layer |
| `aicmo/campaign_ops/service.py` | Business logic |
| `aicmo/campaign_ops/instructions.py` | AI instructions & SOPs |
| `aicmo/campaign_ops/actions.py` | AOL handlers |
| `aicmo/campaign_ops/wiring.py` | Integration layer |
| `aicmo/campaign_ops/ui.py` | Streamlit components |
| `db/alembic/versions/0001_campaign_ops_*.py` | Database migration |

---

## 🔌 Integration Points

### Streamlit UI
- **File:** `streamlit_pages/aicmo_operator.py`
- **Status:** Wrapped in `# AICMO_CAMPAIGN_OPS_WIRING_START/END`
- **Feature Gate:** `AICMO_CAMPAIGN_OPS_ENABLED`

### AOL Daemon
- **File:** `aicmo/orchestration/daemon.py`
- **Handlers:**
  - `CAMPAIGN_TICK` - Daily campaign advancement
  - `ESCALATE_OVERDUE_TASKS` - Weekly overdue escalation
  - `WEEKLY_CAMPAIGN_SUMMARY` - Weekly reporting
- **Status:** Wrapped in `# AICMO_CAMPAIGN_OPS_WIRING_START/END`
- **Preserved:** POST_SOCIAL handler untouched

---

## ✅ Validation Checklist

- [ ] Database migration applied (`alembic upgrade head`)
- [ ] All 6 tables exist in database
- [ ] Feature gate enabled: `AICMO_CAMPAIGN_OPS_ENABLED = True`
- [ ] Validation script passes (10/10 checks)
- [ ] Streamlit UI displays Campaign Operations
- [ ] AOL daemon running with new handlers
- [ ] Test campaign created successfully
- [ ] Tasks generated and marked complete
- [ ] Weekly summary generated without errors
- [ ] No errors in application logs

---

## 🐛 Troubleshooting

| Issue | Fix |
|-------|-----|
| Tables not found | Run `alembic upgrade head` |
| Import errors | Check `aicmo/campaign_ops/__init__.py` |
| UI not showing | Check `AICMO_CAMPAIGN_OPS_ENABLED` |
| Tasks not generated | Verify calendar items exist first |
| AOL handlers not running | Check daemon logs and configuration |
| Syntax errors | Run validation script: `python validation_script.py` |

---

## 📝 Common Workflows

### Create and Run a Campaign

```python
service = CampaignOpsService(session)

# 1. Create campaign
campaign = service.create_campaign(
    "Q4 Product Launch",
    "Complete product launch campaign",
    status="active"
)

# 2. Generate strategic plan
plan = service.generate_plan(
    campaign_id=campaign.id,
    focus_area="Product awareness and adoption",
    duration_days=90
)

# 3. Generate content calendar
calendar = service.generate_calendar(
    plan_id=plan.id,
    content_theme="Educational and promotional content"
)

# 4. Generate operator tasks
tasks = service.generate_tasks_from_calendar(
    calendar_items=calendar,
    assign_to="operator_001"
)

# 5. Get tasks for today
today_tasks = service.get_today_tasks(campaign.id)

# 6. Complete a task
if today_tasks:
    service.mark_task_complete(
        task_id=today_tasks[0].id,
        outcome="Posted successfully with good engagement",
        metrics={"engagement": 150, "clicks": 45}
    )

# 7. Get weekly summary
summary = service.generate_weekly_summary(campaign.id)
print(f"Tasks completed: {summary['tasks_completed']}")
print(f"Engagement rate: {summary['avg_engagement_rate']}")
```

### Check Today's Overdue Tasks

```python
overdue = service.get_overdue_tasks(campaign_id=campaign.id)
print(f"Overdue tasks: {len(overdue)}")
for task in overdue:
    print(f"  - {task.description} (due: {task.due_date})")
```

### Get Campaign Metrics

```python
metrics = service.get_campaign_metrics(campaign_id=campaign.id)
completion_rate = service.get_task_completion_rate(campaign_id=campaign.id)
print(f"Completion rate: {completion_rate:.1%}")
print(f"Metrics: {metrics}")
```

---

## 📊 Database Schema Summary

```sql
-- 6 tables created:
1. campaign_ops_campaigns (root)
2. campaign_ops_plans (per campaign)
3. campaign_ops_calendar_items (per plan)
4. campaign_ops_operator_tasks (per calendar item)
5. campaign_ops_metric_entries (per task)
6. campaign_ops_audit_log (per campaign)

-- Foreign key relationships:
campaigns 1:N plans
plans 1:N calendar_items
calendar_items 1:N operator_tasks
operator_tasks 1:N metric_entries
campaigns 1:N audit_log
```

---

## 🎓 Feature Overview

| Feature | Capability | Status |
|---------|-----------|--------|
| Campaign Management | Create, pause, resume, complete | ✅ Ready |
| AI Plan Generation | Strategic planning with focus areas | ✅ Ready |
| Calendar Generation | Date-based content planning | ✅ Ready |
| Task Generation | Operator-ready actionable tasks | ✅ Ready |
| Platform SOPs | LinkedIn, Instagram, Twitter, Email | ✅ Ready |
| Task Tracking | Status, completion, metrics | ✅ Ready |
| Daily Task Retrieval | Today's and overdue tasks | ✅ Ready |
| Weekly Summaries | Campaign performance reports | ✅ Ready |
| Audit Logging | Complete operation history | ✅ Ready |
| Streamlit UI | Dashboard integration | ✅ Ready |
| AOL Integration | Automated background operations | ✅ Ready |

---

**Ready to deploy! 🚀**

For detailed documentation, see: `CAMPAIGN_OPS_IMPLEMENTATION_GUIDE.md`
