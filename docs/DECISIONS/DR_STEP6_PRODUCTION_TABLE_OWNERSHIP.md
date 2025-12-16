# Decision Record: Production Table Ownership - Step 6

**Date**: 2025-12-13  
**Context**: Phase 4 Lane B Step 6 - Production Module DB Persistence  
**Status**: DECIDED

---

## Decision: C) Both (Reuse + New Tables) with Clear Responsibilities

### Evidence from Discovery

**Existing Production Artifacts:**
```bash
# grep -rn "ProductionAssetDB|production_asset" aicmo
aicmo/production/internal/models.py:26:class ProductionAssetDB(Base):
aicmo/production/internal/models.py:39:    __tablename__ = "production_assets"
```

**Existing Model Structure** ([aicmo/production/internal/models.py](aicmo/production/internal/models.py#L26)):
- Table: `production_assets`
- Purpose: Stage 2 creative assets with publish status tracking
- Fields: campaign_id, platform, format, hook, caption, cta, tone, publish_status, scheduled_date, published_at, meta
- **Problem**: Designed for legacy workflow, NOT aligned with current Production ports/DTOs

**Current Production Ports** ([aicmo/production/api/ports.py](aicmo/production/api/ports.py)):
1. `generate_draft(strategy_id) → ContentDraftDTO`
2. `assemble_bundle(draft_id) → DraftBundleDTO`
3. `get_draft(draft_id) → ContentDraftDTO`

**Current Production DTOs** ([aicmo/production/api/dtos.py](aicmo/production/api/dtos.py)):
- `ContentDraftDTO`: draft_id, strategy_id, content_type, body, metadata, created_at
- `DraftBundleDTO`: bundle_id, draft_id, assets[], assembled_at
- `AssetDTO`: asset_id, asset_type, url, metadata

**Gap Analysis:**
- ✅ `ProductionAssetDB` exists but serves Stage 2 creative publishing (different domain)
- ❌ No table for `ContentDraft` (primary production artifact from ports)
- ❌ No table for `DraftBundle` (assembly coordination)
- ❌ `ProductionAssetDB` schema incompatible with `AssetDTO` fields

---

## Decision Rationale

### Option A: Reuse Existing - REJECTED
**Why Not:**
- `ProductionAssetDB` has campaign_id, platform, format, hook, caption, cta → NOT in current DTOs
- Current DTOs have draft_id, strategy_id, content_type, body → NOT in ProductionAssetDB
- Schema mismatch: cannot reuse for ports contract implementation

### Option B: Add New Tables Only - REJECTED
**Why Not:**
- `ProductionAssetDB` already exists and is used by `aicmo/creatives/service.py` (legacy code)
- Deleting would break existing functionality
- Migration history would lose existing production_assets table

### Option C: Both (Reuse + New) - SELECTED ✅
**Why:**
- Keep `ProductionAssetDB` (production_assets) for legacy Stage 2 creative publishing
- Add NEW tables for ports-aligned persistence:
  - `production_drafts` → `ContentDraftDB`
  - `production_bundles` → `DraftBundleDB`
  - `production_bundle_assets` → `BundleAssetDB` (junction table)

**Clear Responsibilities:**
- **production_assets** (existing): Stage 2 creative publish tracking (legacy, kept for backward compat)
- **production_drafts** (NEW): ContentDraft entities (ports: generate_draft, get_draft)
- **production_bundles** (NEW): DraftBundle entities (ports: assemble_bundle)
- **production_bundle_assets** (NEW): Asset entities within bundles (many-to-one: bundle → assets)

---

## Implementation Plan

### 1. Keep Existing Model
- File: [aicmo/production/internal/models.py](aicmo/production/internal/models.py)
- Model: `ProductionAssetDB` (unchanged)
- Table: `production_assets` (unchanged)
- Purpose: Legacy Stage 2 creative publishing (not touched in Step 6)

### 2. Add New Models (Same File)
```python
class ContentDraftDB(Base):
    __tablename__ = "production_drafts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    draft_id = Column(String, nullable=False, unique=True)  # Idempotency key
    strategy_id = Column(String, nullable=False, index=True)  # Logical FK
    content_type = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

class DraftBundleDB(Base):
    __tablename__ = "production_bundles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    bundle_id = Column(String, nullable=False, unique=True)  # Idempotency key
    draft_id = Column(String, nullable=False, index=True)  # Logical FK to ContentDraft
    assembled_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

class BundleAssetDB(Base):
    __tablename__ = "production_bundle_assets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(String, nullable=False, unique=True)  # Idempotency key
    bundle_id = Column(String, nullable=False, index=True)  # Logical FK to Bundle
    asset_type = Column(String, nullable=False)
    url = Column(String, nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
```

### 3. Idempotency Keys
- **ContentDraft**: `draft_id` (unique constraint)
- **DraftBundle**: `bundle_id` (unique constraint)
- **BundleAsset**: `asset_id` (unique constraint)

**Rationale**: No workflow_run_id in Production DTOs → use entity IDs as idempotency keys

### 4. No Cross-Module FKs
- All references to other modules (strategy_id, campaign_id) are STRING columns (logical FKs)
- No SQLAlchemy ForeignKey or relationship() directives to other modules

---

## Migration Strategy

**New Migration**: `add_production_draft_bundle_tables`

**Upgrade:**
```python
op.create_table('production_drafts', ...)
op.create_table('production_bundles', ...)
op.create_table('production_bundle_assets', ...)
```

**Downgrade:**
```python
op.drop_table('production_bundle_assets')
op.drop_table('production_bundles')
op.drop_table('production_drafts')
```

**Existing Table**: `production_assets` (NOT touched by this migration)

---

## Known Violations (To Fix Later)

**Current Violations Found:**
1. `aicmo/production/api/__init__.py:22` - Exports `ProductionAssetDB` (internal model exposed via API)
2. `aicmo/creatives/service.py:195,199` - Imports `ProductionAssetDB` from production.api (cross-module DB write)

**Phase 4 Lane B Scope:**
- ✅ Add NEW tables for ports-aligned persistence (production_drafts, production_bundles, production_bundle_assets)
- ✅ Keep existing production_assets for legacy compatibility
- ⚠️ Document violations for Phase 4 Lane C cleanup (CAM/Creatives refactor)

---

## Verification Commands

After implementation:
```bash
# Verify model placement
grep -rn "class ContentDraftDB\|class DraftBundleDB\|class BundleAssetDB" aicmo

# Verify no cross-module FKs in new models
grep -n "ForeignKey" aicmo/production/internal/models.py | grep -v "# Logical"

# Verify migration creates only new tables
grep "create_table('production_" db/alembic/versions/<revision>_add_production_draft_bundle_tables.py
```

---

**Decision**: Option C - Both (reuse existing production_assets, add 3 new tables for ports)  
**Approved**: Proceeding with implementation
