# Phase 3: Known CAM DB Models Import Violations

## Status
**Phase 3 Complete**: Core workflow works without CAM violations.  
**Remaining Legacy Code**: 3 files have violations, but are not used by Phase 3 workflow.

## Violations (To Fix in Phase 4)

### 1. aicmo/creatives/service.py:195
- **Location**: Line 195
- **Usage**: `from aicmo.cam.db_models import CreativeAssetDB`
- **Context**: Persisting creative assets to CAM DB during generation
- **Fix**: Replace with CAM command port or CreativeAsset aggregate in Production module
- **Priority**: Medium (used in Kaizen orchestrator, not in Phase 3 workflow)

### 2. aicmo/operator_services.py:19, 1581, 1626
- **Location**: Multiple lines
- **Usage**: Imports `CampaignDB`, `LeadDB`, `ChannelConfigDB`, etc.
- **Context**: Operator Command Center reads CAM data for dashboards
- **Fix**: Replace with CAM query ports
- **Priority**: Low (Command Center UI, not core workflow)

### 3. aicmo/gateways/execution.py:185, 221
- **Location**: Lines 185, 221
- **Usage**: `from aicmo.cam.db_models import ExecutionJobDB`
- **Context**: Gateway writing execution job metadata
- **Fix**: Move ExecutionJobDB to Delivery module or use event bus
- **Priority**: Low (not used in Phase 3 workflow)

## Phase 3 Workflow Status
✅ **client_to_delivery workflow** does NOT use any of these files.
✅ All module adapters use in-memory repos (no CAM DB writes).
✅ CAM adapter stub created for future integration.

## Phase 4 Plan
1. Create CAM aggregate for CreativeAsset management
2. Replace operator_services CAM reads with query ports
3. Move ExecutionJobDB to Delivery module or use event-driven approach
4. Run enforcement test to verify zero violations

## Testing
Run enforcement test:
```bash
pytest tests/enforcement/test_no_cam_db_models_outside_cam.py -v
```

Expected: 3 known violations (documented above).
