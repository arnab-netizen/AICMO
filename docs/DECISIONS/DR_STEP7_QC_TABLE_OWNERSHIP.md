# Decision Record: QC Table Ownership

**Date:** 2025-12-13  
**Status:** DECIDED  
**Context:** Phase 4 Lane B - Step 7 QC Persistence Implementation

## Problem

QC module currently uses only `InMemoryQcRepo`. Need to implement database persistence following Strategy/Production patterns.

## Discovery Evidence

**Grep Results:**
```bash
# Search in aicmo/qc for existing DB code
grep -r "qc_result|qc_results|class.*Qc.*DB|repositories_(db|mem)" aicmo/qc
# Result: NO MATCHES

# Search migrations for existing QC tables
grep -r "create_table('qc_|qc_" db/alembic/versions
# Result: NO MATCHES
```

**File Inspection:**
- `/workspaces/AICMO/aicmo/qc/internal/` contains ONLY:
  - `adapters.py` - InMemoryQcRepo + adapters
  - NO `models.py`
  - NO `repositories_db.py`
  - NO `repositories_mem.py`
  - NO `mappers.py`
  - NO `factory.py`

## Contract Analysis

From `aicmo/qc/api/`:

**Entities:**
- `QcResultDTO`: result_id, draft_id, passed, score, issues[], evaluated_at
- `QcIssueDTO`: severity, section, reason (embedded in result)

**Ports:**
- `QcEvaluatePort.evaluate()` - creates result
- `QcQueryPort.get_result(draft_id)` - retrieves by draft_id

**Idempotency Key:**
- `draft_id` is natural key (one QC result per draft at a time)
- Latest evaluation for a draft should be retrievable

## Decision

**CREATE NEW** QC database persistence following Strategy/Production pattern:

### Tables to Create

**`qc_results`** - Main table
- `result_id` (String, PK) - QcResultId
- `draft_id` (String, indexed, NOT FK) - DraftId (logical reference only)
- `passed` (Boolean)
- `score` (Float)
- `evaluated_at` (DateTime)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**`qc_issues`** - Child table (1:N with qc_results)
- `id` (Integer, PK, autoincrement)
- `result_id` (String, FK to qc_results.result_id)
- `severity` (String) - "critical", "major", "minor"
- `section` (String)
- `reason` (Text)
- `created_at` (DateTime)

### Rationale

1. **No Reuse**: No existing QC tables found
2. **Separate Issues Table**: Issues are variable-length list, needs separate table
3. **No Cross-Module FKs**: `draft_id` stored as String (logical reference to Production module)
4. **Idempotency**: Unique index on `draft_id` for single-result-per-draft semantics
5. **Audit Trail**: Standard `created_at`/`updated_at` columns

### Implementation Files

- `aicmo/qc/internal/models.py` - SQLAlchemy models
- `aicmo/qc/internal/repositories_db.py` - DatabaseQcRepo
- `aicmo/qc/internal/repositories_mem.py` - InMemoryQcRepo (extract from adapters.py)
- `aicmo/qc/internal/mappers.py` - DB ↔ DTO conversion
- `aicmo/qc/internal/factory.py` - Repo factory for dual-mode

### Migration

- New migration: `add_qc_tables`
- Creates: `qc_results`, `qc_issues`
- Zero downtime (additive only)

## Consequences

- QC persistence follows same pattern as Strategy/Production
- Tests: 3 new persistence test files (mem roundtrip, db roundtrip, parity)
- Enforcement: New test `test_no_qc_db_writes_outside_qc.py`
- Composition root: Wire QC repo based on persistence mode

## Cross-Module Boundary Verification

**Allowed:**
- Orchestration composition root imports `aicmo.qc.internal.*` for DI
- No other modules import QC internals

**Forbidden:**
- No cross-module DB foreign keys (draft_id is String, not FK)
- No cross-module internal imports from business logic
