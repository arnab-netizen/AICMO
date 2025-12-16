# Campaign Operations - Complete Implementation Guide

## Overview

Campaign Operations is a comprehensive module for the AICMO system that enables operators to manage social media campaigns with AI-powered task generation, scheduling, and monitoring.

**Key Features:**
- Campaign creation and management
- AI-powered plan generation
- Calendar-based task scheduling  
- Daily task retrieval and completion tracking
- Overdue task escalation
- Weekly campaign summaries
- Platform-specific SOPs (LinkedIn, Instagram, Twitter, Email)
- Full audit logging

## Architecture

### Layered Design
```
┌─────────────────────────────────────┐
│       UI Layer (Streamlit)          │
│       (aicmo_operator.py)            │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│      Service Layer                   │
│  (campaign_ops/service.py)           │
│  - Business logic                    │
│  - Validation                        │
│  - Orchestration                     │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│    Repository Layer                  │
│  (campaign_ops/repo.py)              │
│  - Database access                   │
│  - Query optimization                │
│  - Transaction management            │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│    Data Layer (SQLAlchemy)           │
│  (campaign_ops/models.py)            │
│  - Schema definitions                │
│  - Relationships                     │
│  - Constraints                       │
└─────────────────────────────────────┘
```

### Component Relationships

```
Campaign (root)
├── CampaignPlan (1:N)
│   └── CalendarItem (1:N)
│       └── OperatorTask (1:N)
│           └── MetricEntry (1:N)
│
└── OperatorAuditLog (1:N)
```

## File Structure

```
aicmo/campaign_ops/
├── __init__.py              # Package initialization
├── models.py                # SQLAlchemy models
├── schemas.py               # Pydantic schemas
├── repo.py                  # Repository layer
├── service.py               # Service layer
├── instructions.py          # AI instructions & SOPs
├── actions.py               # AOL action handlers
├── wiring.py                # Integration points
└── ui.py                    # Streamlit UI components

db/alembic/versions/
└── 0001_campaign_ops_...    # Database migration

Configuration:
- Feature gate: AICMO_CAMPAIGN_OPS_ENABLED
- Integration points: streamlit_pages/aicmo_operator.py
                     aicmo/orchestration/daemon.py
```

## Setup Instructions

### 1. Database Migration

Apply the database migration to create all required tables:

```bash
cd /workspaces/AICMO
alembic upgrade head
```

This creates:
- `campaign_ops_campaigns`
- `campaign_ops_plans`
- `campaign_ops_calendar_items`
- `campaign_ops_operator_tasks`
- `campaign_ops_metric_entries`
- `campaign_ops_audit_log`

### 2. Feature Gate

Campaign Ops is controlled by the feature gate `AICMO_CAMPAIGN_OPS_ENABLED`.

To enable:
```python
# In environment or config
AICMO_CAMPAIGN_OPS_ENABLED = True
```

The feature gate is checked in:
- `streamlit_pages/aicmo_operator.py` - UI rendering
- `aicmo/orchestration/daemon.py` - Background operations

### 3. Validation

Run the comprehensive validation script:

```bash
python /workspaces/AICMO/audit_artifacts/campaign_ops_build/validation_script.py
```

This checks:
- File existence
- Python syntax
- Imports
- Models
- Service methods
- Platform SOPs
- AOL handlers
- Wiring
- Migration completeness
- Existing code integrity

## Usage

### Via Python API

```python
from aicmo.campaign_ops.service import CampaignOpsService
from aicmo.database import get_session

session = get_session()
service = CampaignOpsService(session)

# Create a campaign
campaign = service.create_campaign(
    name="Q4 Product Launch",
    description="Complete Q4 product launch campaign",
    status="active",
)

# Generate a plan
plan = service.generate_plan(
    campaign_id=campaign.id,
    focus_area="Product awareness",
    duration_days=90,
)

# Generate calendar
calendar = service.generate_calendar(
    plan_id=plan.id,
    content_theme="Educational posts",
)

# Get today's tasks
tasks = service.get_today_tasks(campaign_id=campaign.id)

# Mark task complete
service.mark_task_complete(
    task_id=tasks[0].id,
    outcome="Posted successfully",
)

# Get weekly summary
summary = service.generate_weekly_summary(campaign_id=campaign.id)
```

### Via Streamlit UI

1. Navigate to the Operator dashboard
2. Select "Campaign Operations" from sidebar
3. Create or select a campaign
4. View dashboard with:
   - Today's tasks
   - Overdue tasks
   - Weekly metrics
   - Campaign status

### Via AOL (Automated Operations Layer)

The daemon automatically:
- Ticks campaigns forward once per day (CAMPAIGN_TICK)
- Escalates overdue tasks weekly (ESCALATE_OVERDUE_TASKS)
- Generates campaign summaries weekly (WEEKLY_CAMPAIGN_SUMMARY)

## Models Reference

### Campaign
Primary entity representing a social media campaign.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | UUID | ✓ | Primary key |
| name | String | ✓ | Campaign name |
| description | Text | | Detailed description |
| status | Enum | ✓ | active/paused/completed |
| created_at | DateTime | ✓ | Auto-set |
| updated_at | DateTime | ✓ | Auto-updated |
| metadata | JSON | | Custom data |

### CampaignPlan
Contains strategic plan for a campaign phase.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | UUID | ✓ | Primary key |
| campaign_id | UUID | ✓ | FK to Campaign |
| phase_number | Int | ✓ | Sequence |
| focus_area | String | ✓ | Strategic focus |
| duration_days | Int | ✓ | Plan duration |
| tactics | JSON | ✓ | Tactical breakdown |
| metrics | JSON | ✓ | Success metrics |

### CalendarItem
Calendar entry for content or activities.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | UUID | ✓ | Primary key |
| plan_id | UUID | ✓ | FK to Plan |
| date | Date | ✓ | Calendar date |
| content_type | String | ✓ | Type of content |
| platform_requirements | JSON | ✓ | Platform-specific specs |
| suggested_posting_time | Time | | Optimal posting time |

### OperatorTask
Actionable task for the operator.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | UUID | ✓ | Primary key |
| calendar_item_id | UUID | ✓ | FK to Calendar |
| platform | Enum | ✓ | linkedin/instagram/twitter/email |
| task_type | Enum | ✓ | write/review/schedule/post |
| description | Text | ✓ | Detailed instructions |
| status | Enum | ✓ | pending/in_progress/completed/failed |
| platform_sop | Text | | Platform-specific SOP |
| assigned_to | String | | Operator identifier |
| due_date | Date | ✓ | Task deadline |
| created_at | DateTime | ✓ | Auto-set |
| updated_at | DateTime | ✓ | Auto-updated |

### MetricEntry
Tracks metrics and outcomes.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | UUID | ✓ | Primary key |
| task_id | UUID | ✓ | FK to Task |
| metric_type | String | ✓ | engagement/reach/clicks/etc |
| value | Float | ✓ | Metric value |
| unit | String | ✓ | %/count/score/etc |
| recorded_at | DateTime | ✓ | Auto-set |

### OperatorAuditLog
Audit trail for all operations.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | UUID | ✓ | Primary key |
| campaign_id | UUID | ✓ | FK to Campaign |
| operator_id | String | ✓ | User identifier |
| action | String | ✓ | Operation performed |
| details | JSON | | Detailed changes |
| timestamp | DateTime | ✓ | Auto-set |

## Service API Reference

### Campaign Management

```python
create_campaign(name, description, status="active", metadata=None)
  → Campaign

get_campaign(campaign_id)
  → Campaign

list_campaigns(status=None, limit=100, offset=0)
  → List[Campaign]

update_campaign(campaign_id, **updates)
  → Campaign

pause_campaign(campaign_id)
  → Campaign

resume_campaign(campaign_id)
  → Campaign

complete_campaign(campaign_id)
  → Campaign
```

### Plan Management

```python
generate_plan(campaign_id, focus_area, duration_days, custom_context=None)
  → CampaignPlan

get_plan(plan_id)
  → CampaignPlan

list_plans(campaign_id)
  → List[CampaignPlan]
```

### Calendar & Tasks

```python
generate_calendar(plan_id, content_theme, custom_context=None)
  → List[CalendarItem]

get_calendar_items(plan_id, start_date=None, end_date=None)
  → List[CalendarItem]

generate_tasks_from_calendar(calendar_items, assign_to=None)
  → List[OperatorTask]

get_today_tasks(campaign_id)
  → List[OperatorTask]

get_overdue_tasks(campaign_id)
  → List[OperatorTask]

mark_task_complete(task_id, outcome="", metrics=None)
  → OperatorTask
```

### Analytics

```python
generate_weekly_summary(campaign_id)
  → Dict[str, Any]

get_campaign_metrics(campaign_id)
  → Dict[str, Any]

get_task_completion_rate(campaign_id)
  → float
```

## Platform SOPs

Campaign Ops includes Standard Operating Procedures for each platform:

### LinkedIn
- Professional tone
- Value-focused content
- Engagement optimization
- Timing: Business hours
- Post format: Multi-line with tags

### Instagram
- Visual emphasis
- Story integration
- Hashtag strategy
- Timing: Peak engagement hours
- Post format: Caption with story hooks

### Twitter
- Concise messaging
- Thread optimization
- Trend awareness
- Timing: Peak engagement hours
- Post format: Character-efficient with threads

### Email
- Personalization
- Subject line optimization
- CTA clarity
- Timing: Open rate optimal times
- Format: HTML with fallback

Each SOP is accessible via:
```python
from aicmo.campaign_ops.instructions import get_platform_sop

sop = get_platform_sop(platform="linkedin", task_type="post")
```

## Integration Points

### Streamlit Dashboard

The campaign ops section appears in the Operator dashboard when feature gate is enabled:

```python
# Location: streamlit_pages/aicmo_operator.py
# Wrapped in: # AICMO_CAMPAIGN_OPS_WIRING_START/END markers
# Does NOT modify existing functionality
```

### AOL Daemon

Three new action handlers integrated into the daemon:

| Handler | Interval | Purpose |
|---------|----------|---------|
| CAMPAIGN_TICK | Daily | Advance campaign timers |
| ESCALATE_OVERDUE_TASKS | Weekly | Alert on overdue items |
| WEEKLY_CAMPAIGN_SUMMARY | Weekly | Generate performance reports |

```python
# Location: aicmo/orchestration/daemon.py
# Wrapped in: # AICMO_CAMPAIGN_OPS_WIRING_START/END markers
# POST_SOCIAL handler preserved and functional
```

## Troubleshooting

### Issue: Tables not created

**Solution:** Run migration
```bash
alembic upgrade head
```

### Issue: Import errors

**Solution:** Verify package structure
```bash
python -m py_compile aicmo/campaign_ops/models.py
python -c "import aicmo.campaign_ops; print('OK')"
```

### Issue: Feature not appearing in UI

**Solution:** Check feature gate
```python
from aicmo.campaign_ops.wiring import AICMO_CAMPAIGN_OPS_ENABLED
print(f"Enabled: {AICMO_CAMPAIGN_OPS_ENABLED}")
```

### Issue: AOL handlers not running

**Solution:** Check daemon configuration
```bash
grep -n "CAMPAIGN_TICK\|ESCALATE_OVERDUE_TASKS\|WEEKLY_CAMPAIGN_SUMMARY" \
  aicmo/orchestration/daemon.py
```

## Testing

### Run Validation Script

```bash
python /workspaces/AICMO/audit_artifacts/campaign_ops_build/validation_script.py
```

Expected output: `✅ ALL CHECKS PASSED - Campaign Ops is ready!`

### Manual Testing

```python
from aicmo.campaign_ops.service import CampaignOpsService
from aicmo.database import get_session

session = get_session()
service = CampaignOpsService(session)

# Test campaign creation
campaign = service.create_campaign("Test Campaign", "Testing", status="active")
print(f"Created: {campaign.id}")

# Test plan generation
plan = service.generate_plan(campaign.id, "Test focus", 30)
print(f"Plan: {plan.id}")

# Test calendar generation
calendar = service.generate_calendar(plan.id, "Test theme")
print(f"Calendar items: {len(calendar)}")

# Test task generation
tasks = service.generate_tasks_from_calendar(calendar[:3])
print(f"Tasks: {len(tasks)}")

print("\n✅ All manual tests passed!")
```

## Maintenance

### Database Backups

Before applying migrations:
```bash
pg_dump aicmo > backup_before_campaign_ops.sql
```

After creating campaigns:
```bash
pg_dump aicmo > backup_with_campaigns.sql
```

### Monitoring

Monitor these metrics:
- Campaign count (growth)
- Task completion rate (efficiency)
- Overdue task count (health)
- AOL handler execution (reliability)

### Cleanup

To remove all campaign data (preserving structure):
```sql
DELETE FROM campaign_ops_metric_entries;
DELETE FROM campaign_ops_audit_log;
DELETE FROM campaign_ops_operator_tasks;
DELETE FROM campaign_ops_calendar_items;
DELETE FROM campaign_ops_plans;
DELETE FROM campaign_ops_campaigns;
```

To fully remove Campaign Ops (rollback):
```bash
alembic downgrade -1
```

## Next Steps

1. **Deploy database migration** - Run `alembic upgrade head`
2. **Enable feature gate** - Set `AICMO_CAMPAIGN_OPS_ENABLED = True`
3. **Run validation** - Execute validation script
4. **Test in Streamlit** - Navigate to Campaign Operations section
5. **Monitor AOL daemon** - Check logs for handler execution
6. **Train operators** - Show dashboard features and capabilities

## Support

For issues or questions:
1. Check validation script for errors
2. Review integration points in wiring.py
3. Consult troubleshooting section above
4. Check audit logs for detailed error traces

---

**Implementation Complete:** ✅
All components ready for deployment and testing.
