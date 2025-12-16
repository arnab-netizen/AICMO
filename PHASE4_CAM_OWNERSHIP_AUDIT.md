# Phase 4 - CAM Ownership Audit Report

**Date**: December 13, 2025  
**Purpose**: Document all CAM data ownership violations before fixing  
**Scope**: Files outside `aicmo/cam/internal/**` that access CAM data

---

## Summary

**Total Violations Found**: 6 occurrences across 3 files  
**Files with Violations**: 3
- `aicmo/creatives/service.py` (1 write)
- `aicmo/gateways/execution.py` (2 writes)
- `aicmo/operator_services.py` (3 reads)

---

## Detailed Violations

### 1. aicmo/creatives/service.py

**Line**: 195  
**Import**: `from aicmo.cam.db_models import CreativeAssetDB`  
**Type**: WRITE  
**Context**: Writing creative asset to CAM table during creative generation

**Code Pattern**:
```python
if campaign_id is not None and session is not None:
    from aicmo.cam.db_models import CreativeAssetDB
    from aicmo.domain.creative import CreativeAsset
    
    asset = CreativeAsset.from_variant(variant, campaign_id=campaign_id)
    db_asset = CreativeAssetDB()
    asset.apply_to_db(db_asset)
    session.add(db_asset)  # WRITE TO CAM TABLE
```

**Proposed Fix**: 
- **Option 1** (Preferred): Move `CreativeAssetDB` model to Production module
  - Rename to `ProductionAssetDB`
  - Creative assets belong to Production domain, not CAM
  - Update schema: `production_assets` table
  - Store `campaign_id` as logical reference (no FK)

- **Option 2** (Alternative): Publish event to CAM
  - Event: `CreativeAssetCreated`
  - CAM subscribes and writes internally
  - More decoupled but adds async complexity

**Recommended**: Option 1 - CreativeAssets are Production domain

---

### 2. aicmo/gateways/execution.py

**Lines**: 185, 221  
**Import**: `from aicmo.cam.db_models import ExecutionJobDB`  
**Type**: WRITE (both)  
**Context**: Queue execution jobs and process them

**First Violation (Line 185)**:
```python
from aicmo.cam.db_models import ExecutionJobDB
from aicmo.domain.execution_job import ExecutionJob

job_ids = []
for content in content_items:
    job = ExecutionJob.from_content_item(content, campaign_id, creative_id)
    db_job = ExecutionJobDB()
    job.apply_to_db(db_job)
    session.add(db_job)  # WRITE TO CAM TABLE
    session.flush()
    job_ids.append(db_job.id)
```

**Second Violation (Line 221)**:
```python
from aicmo.cam.db_models import ExecutionJobDB
from aicmo.domain.execution_job import ExecutionJob

query = session.query(ExecutionJobDB).filter_by(
    campaign_id=campaign_id,
    status="QUEUED"
)
jobs = query.all()  # READ FROM CAM TABLE

for db_job in jobs:
    job = ExecutionJob.from_db(db_job)
    job.status = "IN_PROGRESS"
    # ... process job ...
    db_job.status = job.status  # WRITE TO CAM TABLE
    session.commit()
```

**Proposed Fix**:
- **Option 1** (Preferred): Move `ExecutionJobDB` model to Delivery module
  - Execution jobs are delivery/publishing concerns
  - Rename to `DeliveryJobDB` or `PublishJobDB`
  - Update schema: `delivery_jobs` table
  - Store `campaign_id` as logical reference (no FK)

- **Option 2** (Alternative): Create CAM command/query ports
  - `ExecutionQueueCommandPort.queue_jobs()`
  - `ExecutionQueueQueryPort.get_queued_jobs()`
  - Keeps data in CAM but adds proper boundaries

**Recommended**: Option 1 - Execution jobs belong to Delivery domain

---

### 3. aicmo/operator_services.py

**Lines**: 19, 1581, 1626  
**Import**: `from aicmo.cam.db_models import CampaignDB, LeadDB, OutreachAttemptDB, ContactEventDB, DiscoveryJobDB, SafetySettingsDB, ChannelConfigDB`  
**Type**: READ (all)  
**Context**: Operator Command Center UI reading CAM data for dashboards

**First Violation (Line 19 - module level)**:
```python
from aicmo.cam.db_models import (
    CampaignDB,
    LeadDB,
    OutreachAttemptDB,
    ContactEventDB,
    DiscoveryJobDB,
    SafetySettingsDB,
)
```

**Second Violation (Line 1581)**:
```python
from aicmo.cam.db_models import ChannelConfigDB

config = db.query(ChannelConfigDB).filter(
    ChannelConfigDB.channel == channel_name
).first()  # READ FROM CAM TABLE
```

**Third Violation (Line 1626 - duplicate import)**:
```python
from aicmo.cam.db_models import ChannelConfigDB
# Similar query pattern
```

**Proposed Fix**:
- **Option 1** (Preferred): Replace with CAM query ports
  - Use existing `CampaignQueryPort`, `LeadQueryPort` (to be added)
  - Add `ChannelConfigQueryPort` to CAM API
  - Operator services imports CAM API ports only
  - No direct ORM access

- **Option 2** (Alternative): Create CAM read-only ACL adapter
  - `CamQueryAdapter` exposes read methods
  - Internal implementation uses ORM
  - Operator services uses adapter, not ORM

**Recommended**: Option 1 - Use CAM query ports (proper boundaries)

---

## Data Ownership Analysis

### CAM Should Own:
- ✅ Campaign lifecycle data (CampaignDB)
- ✅ Lead lifecycle data (LeadDB)
- ✅ Outreach attempts (OutreachAttemptDB)
- ✅ Contact events (ContactEventDB)
- ✅ Discovery jobs (DiscoveryJobDB)
- ✅ Safety settings (SafetySettingsDB)
- ✅ Channel configuration (ChannelConfigDB)

### Production Should Own:
- ❌ **CreativeAssetDB** - Currently in CAM, should be in Production
  - Creative assets are production outputs, not CAM data
  - Move to Production module

### Delivery Should Own:
- ❌ **ExecutionJobDB** - Currently in CAM, should be in Delivery
  - Execution/publishing jobs are delivery concerns, not CAM
  - Move to Delivery module

---

## Fix Strategy (Ordered by Priority)

### Phase 1: Move Models to Correct Modules (Breaking but Cleanest)
1. ✅ Move `CreativeAssetDB` → Production module
   - File: `aicmo/production/internal/models.py`
   - Rename: `ProductionAssetDB`
   - Table: `production_assets`
   - Update `creatives/service.py` to use Production model

2. ✅ Move `ExecutionJobDB` → Delivery module
   - File: `aicmo/delivery/internal/models.py`
   - Rename: `DeliveryJobDB`
   - Table: `delivery_jobs`
   - Update `gateways/execution.py` to use Delivery model

3. ✅ Replace operator_services CAM reads with ports
   - Add missing query ports to CAM API
   - Update operator_services to use ports only

### Phase 2: Schema Migration (Alembic)
1. Create migration to rename tables:
   - `creative_assets` → `production_assets`
   - `execution_jobs` → `delivery_jobs`

2. Update foreign key references (if any exist)
   - Replace with logical ID fields (no FK constraints)

### Phase 3: Verification
1. Run enforcement tests → 0 violations
2. Run all tests → all passing
3. Verify Phase 3 workflow still works

---

## Dependencies & Risks

### Dependencies
- Models must be moved before operator_services can be fixed
- Schema migration required for production data

### Risks
- **HIGH**: Schema migration may break existing deployments
  - Mitigation: Create backwards-compatible migration (add new tables, keep old, migrate data, drop old)
  
- **MEDIUM**: ExecutionJobDB may have existing data
  - Mitigation: Data migration script in Alembic revision

- **LOW**: CreativeAssetDB may have foreign key constraints
  - Mitigation: Remove FKs before moving (or make logical references)

---

## Stop Conditions Met?

### Destructive Schema Changes Required?
- ✅ NO - Can use backwards-compatible migrations
- Table renames can be done with:
  1. Create new table
  2. Migrate data
  3. Drop old table

### Will Fixes Break Phase 3 Workflow?
- ✅ NO - Phase 3 workflow doesn't use these files
- Verified: `creatives/service.py`, `gateways/execution.py`, `operator_services.py` not imported by workflow

### Can Fixes Be Completed Without Contract Changes?
- ✅ YES - All fixes use existing patterns:
  - Model moves don't change public APIs
  - Operator services will use existing CAM ports
  - No new port methods needed (or additive only)

---

## Conclusion

**Proceed with fixes**: All violations can be fixed without blocking issues.

**Recommended Approach**:
1. Move CreativeAssetDB to Production module
2. Move ExecutionJobDB to Delivery module  
3. Add CAM query ports for operator_services
4. Create Alembic migrations for schema changes
5. Update enforcement tests to verify fixes

**Estimated Effort**: 2-3 hours for Lane A fixes + testing
