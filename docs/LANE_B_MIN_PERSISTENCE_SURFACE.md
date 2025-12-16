# AICMO Lane B: Minimum Persistence Surface

**Document Purpose**: Define the exact entities requiring database persistence for Phase 4 Lane B.

**Status**: Phase 4 Lane B Step 2  
**Date**: December 13, 2025  
**Scope**: Minimum viable persistence to support core workflow

---

## Guiding Principles

1. **Workflow-Driven**: Only persist entities actively used in ClientToDeliveryWorkflow
2. **No Speculative Work**: Do NOT persist entities that workflow doesn't touch
3. **Incremental**: Start minimal, expand in future phases if needed
4. **Dual-Mode Compatible**: All entities support both `inmemory` and `db` modes

---

## Core Workflow Recap

The ClientToDeliveryWorkflow (Phase 3) executes these steps:

```
1. normalize_brief    (Onboarding)
2. generate_strategy  (Strategy)
3. generate_draft     (Production)
4. qc_evaluate        (QC)
5. create_package     (Delivery)
```

Each step produces artifacts that may need persistence.

---

## Module 1: Onboarding

### Entities to Persist

#### ✅ Brief (NormalizedBriefDTO)
**Why**: Starting point of workflow, referenced by all downstream steps.

**Fields** (from [aicmo/onboarding/api/dtos.py](../aicmo/onboarding/api/dtos.py#L35-L45)):
```python
@dataclass
class NormalizedBriefDTO:
    brief_id: str
    scope: ScopeDTO          # goals, timeline, constraints
    discovery: DiscoveryNotesDTO  # campaign_objective, target_audience, etc.
    metadata: dict
    created_at: datetime
```

**DB Model** (`onboarding_brief` table):
```python
class BriefDB(Base):
    __tablename__ = "onboarding_brief"
    
    id = Column(String, primary_key=True)  # brief_id
    campaign_objective = Column(Text, nullable=False)
    target_audience = Column(Text, nullable=False)
    key_messages = Column(JSON, nullable=False, default=list)  # List[str]
    
    # Scope
    goals = Column(JSON, nullable=False, default=list)
    timeline = Column(String, nullable=True)  # "Q1 2025", etc.
    constraints = Column(JSON, nullable=True, default=dict)
    
    # Metadata
    metadata = Column(JSON, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
```

#### ❌ IntakeFormDTO
**Why NOT**: Workflow calls `brief_normalize` which takes discovery notes, not raw intake. Intake capture is a pre-workflow step.

---

## Module 2: Strategy

### Entities to Persist

#### ✅ Strategy Document (StrategyDocDTO)
**Why**: Core planning artifact, used by production and delivery steps.

**Fields** (from [aicmo/strategy/api/dtos.py](../aicmo/strategy/api/dtos.py#L44-L56)):
```python
class StrategyDocDTO(BaseModel):
    strategy_id: StrategyId
    brief_id: BriefId
    version: int
    kpis: List[KpiDTO]
    channels: List[ChannelPlanDTO]
    timeline: TimelineDTO
    executive_summary: str
    is_approved: bool
    created_at: datetime
    approved_at: Optional[datetime] = None
```

**DB Model** (`strategy_document` table):
```python
class StrategyDocumentDB(Base):
    __tablename__ = "strategy_document"
    
    id = Column(String, primary_key=True)  # strategy_id
    brief_id = Column(String, nullable=False)  # Logical reference, no FK
    version = Column(Integer, nullable=False)  # Version number
    
    # Strategy content (JSON serialized)
    kpis = Column(JSON, nullable=False, default=list)  # List[dict] (serialized KpiDTO)
    channels = Column(JSON, nullable=False, default=list)  # List[dict] (serialized ChannelPlanDTO)
    timeline = Column(JSON, nullable=False)  # dict (serialized TimelineDTO)
    executive_summary = Column(Text, nullable=False)
    
    # Approval tracking
    is_approved = Column(Boolean, nullable=False, default=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    
    # Unique constraint for idempotency: (brief_id, version) must be unique
    __table_args__ = (
        UniqueConstraint('brief_id', 'version', name='uq_strategy_brief_version'),
    )
```

#### ❌ StrategyVersionDTO
**Why NOT**: Versioning is useful but not required for minimum viable workflow. Add in future phase if needed.

---

## Module 3: Production

### Entities to Persist

**Decision Reference**: [DR_STEP6_PRODUCTION_TABLE_OWNERSHIP.md](DECISIONS/DR_STEP6_PRODUCTION_TABLE_OWNERSHIP.md)  
**Strategy**: Option C - Both (reuse existing + add new tables for ports-aligned persistence)

#### ✅ ContentDraft (ContentDraftDTO)
**Why**: Primary production artifact generated from strategy, required for workflow step 3 (generate_draft).

**Fields** (from [aicmo/production/api/dtos.py](../aicmo/production/api/dtos.py#L7-L14)):
```python
class ContentDraftDTO(BaseModel):
    draft_id: DraftId
    strategy_id: StrategyId
    content_type: str
    body: str
    metadata: Dict[str, Any] = {}
    created_at: datetime
```

**DB Model** (`production_drafts` table):
```python
class ContentDraftDB(Base):
    __tablename__ = "production_drafts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    draft_id = Column(String, nullable=False, unique=True)  # Idempotency key
    strategy_id = Column(String, nullable=False, index=True)  # Logical FK
    content_type = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
```

**Idempotency Key**: `draft_id` (unique constraint)  
**Compensation Policy**: DELETE (draft generation can be retried without state accumulation)

---

#### ✅ DraftBundle (DraftBundleDTO)
**Why**: Assembly coordination for draft + assets, supports assemble_bundle port method.

**Fields** (from [aicmo/production/api/dtos.py](../aicmo/production/api/dtos.py#L23-L28)):
```python
class DraftBundleDTO(BaseModel):
    bundle_id: str
    draft_id: DraftId
    assets: List[AssetDTO]
    assembled_at: datetime
```

**DB Model** (`production_bundles` table):
```python
class DraftBundleDB(Base):
    __tablename__ = "production_bundles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bundle_id = Column(String, nullable=False, unique=True)  # Idempotency key
    draft_id = Column(String, nullable=False, index=True)  # Logical FK to ContentDraft
    assembled_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
```

**Idempotency Key**: `bundle_id` (unique constraint)  
**Compensation Policy**: DELETE (assembly can be retried without state accumulation)

---

#### ✅ BundleAsset (AssetDTO)
**Why**: Creative assets within bundles, many-to-one relationship with DraftBundle.

**Fields** (from [aicmo/production/api/dtos.py](../aicmo/production/api/dtos.py#L18-L22)):
```python
class AssetDTO(BaseModel):
    asset_id: AssetId
    asset_type: str
    url: str
    metadata: Dict[str, Any] = {}
```

**DB Model** (`production_bundle_assets` table):
```python
class BundleAssetDB(Base):
    __tablename__ = "production_bundle_assets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(String, nullable=False, unique=True)  # Idempotency key
    bundle_id = Column(String, nullable=False, index=True)  # Logical FK to Bundle
    asset_type = Column(String, nullable=False)
    url = Column(String, nullable=False)
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
```

**Idempotency Key**: `asset_id` (unique constraint)  
**Compensation Policy**: DELETE (assets regenerated with bundle)

---

#### ✅ ProductionAssetDB (Legacy - Already Exists)
**Status**: ALREADY IMPLEMENTED in [aicmo/production/internal/models.py](../aicmo/production/internal/models.py#L26)  
**Table**: `production_assets`  
**Purpose**: Stage 2 creative publishing with campaign linkage (legacy workflow, NOT used by current ports)

**Note**: This model exists from earlier work, serves different domain (creative publishing vs. draft generation).

**Decision for Lane B**: Keep as-is for backward compatibility, NOT used for ports-aligned persistence.

**Known Violations** (documented for future cleanup):
- Exported via `aicmo/production/api/__init__.py` (internal model exposed)
- Used by `aicmo/creatives/service.py` (cross-module DB write)

---

### Production Persistence Summary

**New Tables for Ports** (3):
1. `production_drafts` → ContentDraftDB
2. `production_bundles` → DraftBundleDB
3. `production_bundle_assets` → BundleAssetDB

**Existing Table** (1, unchanged):
4. `production_assets` → ProductionAssetDB (legacy, not touched)

**Idempotency Strategy**:
- No `workflow_run_id` in Production DTOs
- Use entity IDs as idempotency keys: draft_id, bundle_id, asset_id
- Enforce via UNIQUE constraints at DB level

---

## Module 4: QC

### Entities to Persist

**Decision Reference**: [DR_STEP7_QC_TABLE_OWNERSHIP.md](DECISIONS/DR_STEP7_QC_TABLE_OWNERSHIP.md)  
**Strategy**: Create new tables (no existing QC persistence found)

#### ✅ QC Result (QcResultDTO)
**Why**: QC evaluation determines workflow continuation, must be retrievable for audit.

**Fields** (from [aicmo/qc/api/dtos.py](../aicmo/qc/api/dtos.py#L16-L25)):
```python
class QcResultDTO(BaseModel):
    result_id: QcResultId
    draft_id: DraftId
    passed: bool
    score: float
    issues: List[QcIssueDTO]
    evaluated_at: datetime
```

**DB Model** (`qc_results` table):
```python
class QcResultDB(Base):
    __tablename__ = "qc_results"
    
    id = Column(String, primary_key=True)  # result_id (QcResultId)
    draft_id = Column(String, nullable=False, unique=True, index=True)  # Logical FK, idempotency key
    
    # Evaluation results
    passed = Column(Boolean, nullable=False)
    score = Column(Float, nullable=False)
    evaluated_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
```

**Idempotency Key**: `draft_id` (unique constraint - one QC result per draft)  
**Compensation Policy**: DELETE or mark as superseded (re-evaluation replaces previous result)

---

#### ✅ QC Issue (QcIssueDTO)
**Why**: Variable-length list of quality issues found during evaluation.

**Fields** (from [aicmo/qc/api/dtos.py](../aicmo/qc/api/dtos.py#L12-L15)):
```python
class QcIssueDTO(BaseModel):
    severity: str  # "critical", "major", "minor"
    section: str
    reason: str
```

**DB Model** (`qc_issues` table):
```python
class QcIssueDB(Base):
    __tablename__ = "qc_issues"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    result_id = Column(String, ForeignKey("qc_results.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Issue details
    severity = Column(String, nullable=False)  # "critical", "major", "minor"
    section = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
```

**Relationship**: Many-to-one with QcResultDB (cascade delete on parent removal)

---

### QC Rollback/Compensation Semantics

**On QC Failure in Workflow:**
1. QC result stored with `passed=False`
2. Workflow compensation triggered
3. Draft generation rolled back (draft deleted)
4. QC result remains in DB for audit (shows why workflow failed)

**On Re-evaluation:**
- New evaluation for same draft_id → update existing result (idempotent)
- OR: Delete old result and create new (depending on repo implementation)
- Issues cascade deleted when parent result deleted

**Audit Trail:**
- `updated_at` tracks when result was last modified
- Issues remain immutable once created (deleted only with parent)

---

## Module 5: Delivery

### Entities to Persist

#### ✅ Delivery Package (DeliveryPackageDTO)
**Why**: Final workflow output, contains all deliverables for client.

**Fields** (inferred from workflow):
```python
@dataclass
class DeliveryPackageDTO:
    package_id: str
    draft_id: str
    qc_result_id: str
    artifacts: list[ArtifactDTO]  # Packaged deliverables
    status: str  # "READY", "DELIVERED", "FAILED"
    created_at: datetime
```

**DB Model** (`delivery_package` table):
```python
class DeliveryPackageDB(Base):
    __tablename__ = "delivery_package"
    
    id = Column(String, primary_key=True)  # package_id
    draft_id = Column(String, nullable=False)  # Logical reference, no FK
    qc_result_id = Column(String, nullable=False)  # Logical reference, no FK
    
    # Package contents
    artifacts = Column(JSON, nullable=False, default=list)  # List[dict] (serialized ArtifactDTO)
    
    # Status tracking
    status = Column(String, nullable=False, default="READY")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
```

#### ✅ DeliveryJobDB (Already Exists)
**Status**: ALREADY IMPLEMENTED in [aicmo/delivery/internal/models.py](../aicmo/delivery/internal/models.py)

**Note**: Similar to ProductionAssetDB, may need convention updates later.

**Decision for Lane B**: Keep as-is for now.

---

## Module 6: CAM

### Entities to Persist

#### ⚠️ ALREADY PERSISTED
**Status**: CAM has ~30 DB models in [aicmo/cam/db_models.py](../aicmo/cam/db_models.py), already implemented.

**Lane B Scope**: NO NEW CAM PERSISTENCE WORK REQUIRED.

**Note**: CAM models may need convention updates (e.g., server_default → default), but that's post-Lane B cleanup.

---

## Entities NOT Persisting (Explicitly Deferred)

### ❌ Saga Execution State
**Rationale**: Saga state is ephemeral workflow orchestration state. Sagas are short-lived (seconds to minutes). If needed for audit/debugging, add in future phase.

### ❌ Event History (EventBus)
**Rationale**: In-memory event bus for intra-process pub/sub. Events are not domain entities. If event sourcing needed, add in future phase.

### ❌ WorkflowState
**Rationale**: Transient coordination state inside workflow execution. Not a persistent entity.

### ❌ Module Query Adapters
**Rationale**: Query adapters read from repos, don't introduce new entities.

---

## Implementation Order

Following the workflow execution order for intuitive incremental testing:

1. **Onboarding**: Brief persistence
2. **Strategy**: StrategyDocument persistence
3. **Production**: Draft persistence (ProductionAssetDB already exists)
4. **QC**: QcResult persistence
5. **Delivery**: DeliveryPackage persistence (DeliveryJobDB already exists)

---

## Verification Criteria

After implementing each module:

✅ **Repository Tests**: Save/load operations work in both modes  
✅ **Workflow Test**: E2E workflow runs with db mode  
✅ **Determinism**: `inmemory` and `db` modes produce identical outputs  
✅ **Migration Applied**: Alembic migration created and applied  
✅ **No Leakage**: DB models never escape module boundaries

---

## Summary Table

| Module | Entity | Table Name | Status | Dependencies |
|--------|--------|-----------|--------|--------------|
| Onboarding | Brief | `onboarding_brief` | ✅ IMPLEMENTED | None |
| Strategy | StrategyDocument | `strategy_document` | ✅ IMPLEMENTED | brief_id |
| Production | ContentDraft | `production_drafts` | ✅ TO IMPLEMENT | strategy_id |
| Production | DraftBundle | `production_bundles` | ✅ TO IMPLEMENT | draft_id |
| Production | BundleAsset | `production_bundle_assets` | ✅ IMPLEMENTED | bundle_id |
| Production | ProductionAsset | `production_assets` | ✅ ALREADY EXISTS (legacy) | campaign_id |
| QC | QcResult | `qc_results` | ✅ IMPLEMENTED | draft_id |
| QC | QcIssue | `qc_issues` | ✅ IMPLEMENTED | result_id |
| Delivery | DeliveryPackage | `delivery_package` | 🔜 TO IMPLEMENT | draft_id, qc_result_id |
| Delivery | DeliveryJob | `delivery_jobs` | ✅ ALREADY EXISTS | campaign_id, creative_id |
| CAM | (30+ models) | `campaigns`, `leads`, etc. | ✅ ALREADY EXISTS | N/A |

**Completed**: 3 modules (Onboarding, Strategy, QC)  
**In Progress**: 1 module (Production - Step 6)  
**Total New Tables**: 10 (4 completed + 3 production + 3 future)

---

## Next Steps

Proceed to **Step 3: Configuration Setup** to add AICMO_PERSISTENCE_MODE environment variable support.

---

**End of Document**
