# DISCOVERY SUMMARY: Cascade Lineage Bug

## Problem Statement
Downstream artifacts store `source_versions.strategy = 1` (the version at creation time).
When strategy is revised to v2 (draft), then approved as v3, the cascade logic incorrectly compares against saved version, not approved version.

## Failing Scenario (test_multi_level_cascade - SKIPPED)
1. Create and approve Strategy v1 (derived from Intake approved v1)
2. Create Creatives artifact using Strategy approved v1 → stores `source_versions.strategy = 1`
3. Update Strategy to v2 as revised (NOT approved) → creatives should NOT be flagged (draft changes don't cascade)
4. Approve Strategy as v3 → creatives SHOULD be flagged (approved version changed from 1 to 3)

**CURRENT BUG:** Cascade compares `downstream.source_versions[upstream] < upstream.version`, which breaks when drafts exist.

## Current Lineage Mechanism (BROKEN)

### Lines involved:
- `artifact_store.py:169` - Records `source_versions[source.artifact_type.value] = source.version` (ANY version, not approved)
- `artifact_store.py:314-318` - Cascade checks `old_version < upstream_artifact.version` (compares to CURRENT version, not approved)
- `artifact_store.py:191-220` - `update_artifact()` triggers cascade on version increment (triggered by draft saves too)
- `artifact_store.py:235-271` - `approve_artifact()` does NOT trigger cascade when approving a new version

### Why it breaks:
1. **Creation records arbitrary version:** When creating downstream, it records `source.version` (could be v2 draft, v3 draft, etc.)
2. **No approved lineage tracking:** No field stores "which approved version was this derived from"
3. **Cascade triggers on version bump:** Any `update_artifact(increment_version=True)` triggers cascade, even for drafts
4. **Approval doesn't cascade:** When approving v3, no cascade happens because approval doesn't check if it's a NEW approved version

## Root Causes
1. **Missing approved lineage:** Need `source_lineage` dict with `{artifact_type: {approved_version: X, approved_at: ISO}}`
2. **Cascade trigger wrong:** Should trigger on `approve_artifact()` when new approved version > previous approved version
3. **No "latest approved version" helper:** Can't determine current approved version per type
4. **Backward compat missing:** Existing artifacts have `source_versions`, need migration shim

## Functions to Modify
1. `Artifact.__init__` - Add `source_lineage` field
2. `ArtifactStore.create_artifact()` - Record approved lineage from source artifacts
3. `ArtifactStore.approve_artifact()` - Trigger cascade on new approved version
4. `ArtifactStore.update_artifact()` - Remove cascade trigger (or make conditional)
5. `ArtifactStore.cascade_on_upstream_change()` - Compare approved lineage, not saved version
6. `ArtifactStore._compute_inputs_hash()` - Hash approved lineage, not arbitrary versions
7. NEW: `ArtifactStore.get_latest_approved()` - Get latest approved artifact by type
8. NEW: `ArtifactStore.get_current_approved_version_map()` - Get approved version map
9. NEW: `Artifact.from_dict()` - Backward compat shim for source_lineage

## Test to Restore
- `tests/test_artifact_store_cascade.py::TestCascadeLogic::test_multi_level_cascade` (currently skipped)

## Expected Behavior After Fix
1. Draft saves do NOT trigger cascade
2. Approvals trigger cascade ONLY if approved version is new/higher
3. Downstream records approved lineage at creation time
4. Staleness checks compare against approved lineage map
5. Multi-level cascade works correctly
