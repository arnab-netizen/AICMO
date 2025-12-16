# Campaign Ops Deployment Guide

## Quick Start

Campaign Ops database migration is ready. Execute this command to deploy:

```bash
bash scripts/apply_campaign_ops_migrations.sh
```

Expected output:
```
✅ Migrations applied successfully
Campaign Ops tables: 6/6
✅ All Campaign Ops tables exist!
✅ SUCCESS: Campaign Ops database is ready!
```

## What Gets Created

6 PostgreSQL tables with indexes and foreign keys:
1. `campaign_ops_campaigns` - Campaign metadata
2. `campaign_ops_plans` - Strategic plans
3. `campaign_ops_calendar_items` - Campaign timeline
4. `campaign_ops_operator_tasks` - Action items
5. `campaign_ops_metric_entries` - Performance metrics
6. `campaign_ops_audit_log` - Change history

## Environment Setup

### Required Environment Variable
```bash
DATABASE_URL="postgresql://user:password@host:5432/database?sslmode=require"
```

For Neon PostgreSQL (current setup):
```bash
DATABASE_URL="postgresql://neondb_owner:password@ep-sweet-hat-ad3o70vb-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
```

### Optional
```bash
AICMO_ENV=production  # Default: development
```

## Deployment Steps

### Step 1: Verify Environment
```bash
echo $DATABASE_URL  # Should show database URL
```

### Step 2: Apply Migrations
```bash
cd /workspaces/AICMO
bash scripts/apply_campaign_ops_migrations.sh
```

The script will:
- Parse DB connection info
- Run `alembic upgrade head`
- Verify all 6 tables exist
- Display success or failure clearly

### Step 3: Verify Tables (Optional)
```bash
python3 audit_artifacts/campaign_ops_fix/verify_campaign_ops_tables.py
```

Exit code: `0` = Success, `1` = Missing tables

### Step 4: Restart Services
In this order:
1. Backend API (if running separately)
2. AOL daemon (background worker)
3. Streamlit operator dashboard

## Troubleshooting

### Error: "Multiple head revisions are present"
**Cause**: Migration dependency chain broken  
**Fix**: This has been fixed in the migration file. No action needed.

### Error: "Tables not created"
**Cause**: Migration script didn't execute  
**Check**:
```bash
# Verify DATABASE_URL is set
echo $DATABASE_URL

# Run verification script
python3 audit_artifacts/campaign_ops_fix/verify_campaign_ops_tables.py

# Check Alembic status
alembic current
alembic heads
```

### Error: "Permission denied" on script
```bash
chmod +x scripts/apply_campaign_ops_migrations.sh
bash scripts/apply_campaign_ops_migrations.sh
```

## Features Available After Deployment

### Operator Dashboard
- Create new campaigns
- View all campaigns by status
- Generate strategic plans and calendar
- View operator tasks and due dates
- Mark tasks as complete
- Generate weekly summaries

### Background Processing
AOL daemon handles:
- Periodic campaign ticks (CAMPAIGN_TICK)
- Escalation of overdue tasks (ESCALATE_OVERDUE_TASKS)
- Weekly summary generation (WEEKLY_CAMPAIGN_SUMMARY)

### Feature Control
Campaign Ops is enabled by default:
```python
AICMO_CAMPAIGN_OPS_ENABLED = True
```

To disable:
```python
AICMO_CAMPAIGN_OPS_ENABLED = False
```

## Rollback

To undo the migration:
```bash
alembic downgrade d2f216c8083f  # Go back to before Campaign Ops migration
```

This will:
- Drop all 6 Campaign Ops tables
- Preserve all other tables
- Database stays in consistent state

## Verification Evidence

All artifacts preserved in `audit_artifacts/campaign_ops_fix/`:
- `apply_migrations_log.txt` - Migration execution log
- `service_smoke_log.txt` - Service layer validation
- `verify_campaign_ops_tables.py` - Verification script
- `CAMPAIGN_OPS_FIX_COMPLETE.md` - Detailed report

## Support

For issues or questions:
1. Check migration log: `tail audit_artifacts/campaign_ops_fix/apply_migrations_log.txt`
2. Run verification: `python3 audit_artifacts/campaign_ops_fix/verify_campaign_ops_tables.py`
3. Check DB diagnostics: Visible in Streamlit UI under Campaign Ops tab
4. Review complete report: `audit_artifacts/campaign_ops_fix/CAMPAIGN_OPS_FIX_COMPLETE.md`
