# Decision Record: Step 8 - Delivery Table Ownership

**Date:** December 13, 2025  
**Status:** Accepted  
**Context:** Phase 4 Lane B - Delivery Module Database Persistence

---

## Decision

The Delivery module will own two new database tables:
- `delivery_packages` (parent)
- `delivery_artifacts` (child)

No cross-module foreign keys will be created. The `draft_id` field will be stored as a `String` for logical reference only.

---

## Context

### Pre-Decision Discovery

Searched for existing Delivery persistence:

```bash
grep -r "DeliveryPackageDB\|delivery_packages" aicmo/
# Result: NONE - no existing DB models

grep -r "class.*Delivery.*Repo" aicmo/delivery/
# Result: InMemoryDeliveryRepo in adapters.py (Phase 3 baseline)
```

**Finding:** Delivery module currently uses in-memory storage only (`InMemoryDeliveryRepo` in `adapters.py`). No database tables exist.

### Existing DTO Structure

From `aicmo/delivery/api/dtos.py`:

```python
class DeliveryArtifactDTO(BaseModel):
    name: str
    url: str
    format: str

class DeliveryPackageDTO(BaseModel):
    package_id: DeliveryPackageId  # Primary identifier
    draft_id: DraftId             # Logical reference to Production module
    artifacts: List[DeliveryArtifactDTO]  # 1:N relationship
    created_at: datetime
```

**Key Observations:**
1. `package_id` is the primary entity identifier
2. `draft_id` references the Production module (logical link only)
3. `artifacts` is a child collection (ordered list)
4. No workflow_run_id in DTO (unlike Onboarding)

---

## Decision Rationale

### 1. Create New Tables

**Why not reuse existing tables?**
- No existing `delivery_packages` or `delivery_artifacts` tables
- No legacy delivery persistence infrastructure
- Clean slate implementation following established pattern

**Table Design:**

**delivery_packages:**
- `id` (PK, autoincrement) — database surrogate key
- `package_id` (String, unique, indexed) — business key, idempotency anchor
- `draft_id` (String, NOT a foreign key) — logical reference to production.production_drafts
- `created_at` (DateTime)
- `updated_at` (DateTime)

**delivery_artifacts:**
- `id` (PK, autoincrement) — database surrogate key
- `package_id` (String, NOT a foreign key) — parent reference
- `name` (String) — artifact filename
- `url` (String) — artifact URL
- `format` (String) — file format (zip, pdf, etc.)
- `position` (Integer) — ordering within package (for deterministic retrieval)
- `created_at` (DateTime)

### 2. No Cross-Module Foreign Keys

**Rule:** Draft ID stored as String, not a foreign key to `production_drafts`.

**Why?**
- **Decoupling:** Delivery module does not depend on Production module's database schema
- **Independent Evolution:** Tables can be altered without cross-module coordination
- **Enforcement:** Phase 4 boundary rule (no DB FKs across module boundaries)
- **Pattern Consistency:** Same approach used in Strategy, Production, QC modules

**Verification:**
- Automated by `test_no_delivery_db_writes_outside_delivery.py`
- No SQLAlchemy `ForeignKey()` crossing module boundaries

### 3. Idempotency Strategy

**Key:** `package_id` (unique constraint)

**Semantics:** "Latest package wins"

**Implementation:**
```python
def save_package(self, package_dto: DeliveryPackageDTO) -> None:
    with self._get_session() as session:
        # Delete existing package + artifacts (cascade)
        existing = session.query(DeliveryPackageDB).filter_by(
            package_id=package_dto.package_id
        ).first()
        if existing:
            session.delete(existing)
            session.flush()
        
        # Insert new package + artifacts
        new_package = dto_to_db(package_dto)
        session.add(new_package)
        session.commit()
```

**Rationale:**
- Same draft may be delivered multiple times (re-delivery)
- Latest delivery package replaces previous one
- Cascade delete ensures orphaned artifacts are removed
- Deterministic behavior across mem and db repos

### 4. Artifact Ordering

**Challenge:** List order must be deterministic across mem and db.

**Solution:** Add `position` field to `delivery_artifacts` table.

**Implementation:**
- Save: Assign position based on list index (0, 1, 2, ...)
- Retrieve: `ORDER BY position ASC` in SQL query
- In-Memory: Return artifacts in original list order (no sorting needed if stored in dict/list)

**Verification:**
- Parity tests compare artifact order
- Canonicalization function sorts by position/name for comparison

### 5. Artifact Replacement Semantics

**Scenario:** Saving same `package_id` twice with different artifacts.

**Behavior:**
1. Delete existing `DeliveryPackageDB` record
2. Cascade delete removes all associated `DeliveryArtifactDB` records
3. Insert new package + new artifacts

**Rationale:**
- Simplifies artifact management (no manual cleanup)
- Ensures no orphaned artifacts
- Matches production module pattern (bundle assets replaced on re-save)

---

## Alternatives Considered

### Alternative 1: Reuse Production Module Tables

**Considered:** Store delivery packages as a view over `production_drafts` + `production_bundle_assets`.

**Rejected:**
- Delivery artifacts are different from production assets (URLs vs content)
- Delivery has its own lifecycle (publishing, versioning)
- Violates module separation of concerns

### Alternative 2: Store Artifacts as JSON in Single Table

**Considered:** Store `artifacts` as JSONB column in `delivery_packages`.

**Rejected:**
- Loses relational query capability
- Makes artifact-level enforcement harder
- Inconsistent with established pattern (Production uses separate assets table)
- Ordering becomes implicit (JSON array order)

### Alternative 3: Cross-Module Foreign Key to production_drafts

**Considered:** `draft_id` as FK to `production.production_drafts.draft_id`.

**Rejected:**
- Violates Phase 4 hard rule (no cross-module FKs)
- Creates tight coupling between Delivery and Production databases
- Would fail enforcement test `test_no_delivery_db_writes_outside_delivery.py`

---

## Consequences

### Positive

✅ **Decoupled Persistence:** Delivery module owns its tables, no external dependencies  
✅ **Idempotent Saves:** Same package_id can be saved multiple times safely  
✅ **Deterministic Ordering:** Artifacts always retrieved in same order  
✅ **Cascade Delete:** No orphaned artifacts when package is replaced  
✅ **Pattern Consistency:** Matches Strategy/Production/QC implementation rigor  

### Negative

⚠️ **Referential Integrity:** No database-enforced link to `production_drafts` (logical reference only)  
⚠️ **Artifact Duplication:** Separate table adds storage overhead vs JSON column  

### Mitigations

- **Referential Integrity:** Enforce at application layer (workflow orchestration)
- **Storage Overhead:** Acceptable trade-off for relational query capability and consistency

---

## Implementation Checklist

- [x] Decision documented
- [ ] Tables created in migration
- [ ] DB repository implemented
- [ ] In-memory repository extracted
- [ ] Mappers created
- [ ] Factory created
- [ ] Composition root wired
- [ ] 20 persistence tests created (7 mem + 8 db + 5 parity)
- [ ] Enforcement test updated
- [ ] E2E cleanup fixture updated
- [ ] All 168+ tests passing

---

## References

- **Similar Decisions:**
  - [DR_STEP7_QC_TABLE_OWNERSHIP.md](DR_STEP7_QC_TABLE_OWNERSHIP.md)
  - Production module implementation (Step 6)
  - Strategy module implementation (Step 5)

- **Relevant Files:**
  - `aicmo/delivery/api/dtos.py` (DTOs unchanged)
  - `aicmo/delivery/internal/adapters.py` (existing in-memory repo)
  - `aicmo/orchestration/composition/root.py` (composition wiring)

---

**Approved By:** Systematic implementation following Phase 4 Lane B pattern  
**Next Step:** Implement `aicmo/delivery/internal/models.py`
