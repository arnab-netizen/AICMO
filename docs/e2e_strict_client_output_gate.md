# AICMO Strict Client Output E2E Gate

**Version:** 1.0.0  
**Status:** IMPLEMENTATION IN PROGRESS  
**Last Updated:** 2025-12-15

## Purpose

This E2E gate ensures that **if Playwright tests are GREEN, AICMO is safe to deliver client-facing outputs in real usage.**

Any test failure means AICMO is NOT safe for client delivery.

## Quick Start

### Prerequisites

```bash
# Required environment variables
export AICMO_E2E_MODE=1
export AICMO_E2E_DIAGNOSTICS=1
export AICMO_PROOF_RUN=1
export AICMO_PERSISTENCE_MODE=db
export AICMO_TEST_SEED=e2e-deterministic-seed-2025
export AICMO_E2E_ARTIFACT_DIR=/workspaces/AICMO/artifacts/e2e
```

### Run Full E2E Suite

```bash
cd /workspaces/AICMO

# Start Streamlit with E2E config
./scripts/start_e2e_streamlit.sh

# Run Playwright tests
npm run test:e2e:strict

# Check validation reports
./scripts/check_e2e_validation.sh
```

### CI Command

```bash
./scripts/ci_e2e_gate.sh
```

## Scope Definition

### Client-Facing Outputs (IN SCOPE)

See [docs/e2e_client_output_inventory.md](e2e_client_output_inventory.md) for exhaustive list.

Summary:
- PDF reports
- PPTX presentations
- DOCX documents
- CSV data exports
- Email/message previews
- ZIP archives

### Not Client-Facing (OUT OF SCOPE)

- Internal logs
- Diagnostics panels
- Debug traces
- System metadata
- Raw LLM prompts

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT REQUEST                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              AICMO Generator Pipeline                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Generate   │→ │  Section Map │→ │   Artifact   │      │
│  │   Content    │  │   Creation   │  │   Creation   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Validation Pipeline (GATE)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Structural  │→ │    Safety    │→ │   Content    │      │
│  │  Validation  │  │  Validation  │  │  Validation  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                           │                                  │
│                           ▼                                  │
│              ┌─────────────────────────┐                     │
│              │  Validation Report      │                     │
│              │  (PASS/FAIL)            │                     │
│              └─────────────────────────┘                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ├─ PASS → ┌──────────────────────┐
                       │          │  Artifact Manifest   │
                       │          │  Delivery Enabled    │
                       │          └──────────────────────┘
                       │
                       └─ FAIL → ┌──────────────────────┐
                                 │  Delivery BLOCKED    │
                                 │  Error Report        │
                                 └──────────────────────┘
```

## Components

### 1. Output Inventory
**Location:** `docs/e2e_client_output_inventory.md`  
**Status:** ✅ IMPLEMENTED

Exhaustive list of all client-facing outputs with metadata.

### 2. Output Contracts
**Location:** `tests/e2e/specs/client_outputs.contract.json`  
**Status:** ✅ IMPLEMENTED

Machine-readable validation rules for each output type.

### 3. Section Map Generator
**Location:** `aicmo/validation/section_map.py`  
**Status:** ⏳ PENDING

Generates structured section maps at generation time:
- Section IDs
- Section titles
- Word counts
- Content hashes
- Section order

### 4. Artifact Manifest
**Location:** `aicmo/validation/manifest.py`  
**Status:** ⏳ PENDING

Schema:
```json
{
  "manifest_version": "1.0.0",
  "run_id": "uuid",
  "client_id": "client-123",
  "project_id": "project-456",
  "timestamp": "2025-12-15T10:30:00Z",
  "artifacts": [
    {
      "artifact_id": "marketing_strategy_report_pdf",
      "filename": "marketing_strategy_report.pdf",
      "path": "artifacts/e2e/run-uuid/marketing_strategy_report.pdf",
      "size_bytes": 1234567,
      "checksum_sha256": "abc123...",
      "schema_version": "1.0.0",
      "format": "pdf"
    }
  ]
}
```

### 5. Validation Report
**Location:** `aicmo/validation/validator.py`  
**Status:** ⏳ PENDING

Schema:
```json
{
  "validation_version": "1.0.0",
  "run_id": "uuid",
  "timestamp": "2025-12-15T10:30:05Z",
  "global_status": "PASS",
  "artifacts": [
    {
      "artifact_id": "marketing_strategy_report_pdf",
      "status": "PASS",
      "structural_checks": {
        "readable": true,
        "page_count": 15,
        "page_count_valid": true,
        "metadata_present": true
      },
      "safety_checks": {
        "no_placeholders": true,
        "no_forbidden_phrases": true,
        "no_path_traversal": true
      },
      "content_checks": {
        "required_sections_present": true,
        "word_counts_valid": true,
        "required_strings_present": true
      },
      "section_validations": [
        {
          "section_id": "executive_summary",
          "title": "Executive Summary",
          "word_count": 287,
          "word_count_valid": true,
          "placeholder_scan": "PASS",
          "forbidden_phrase_scan": "PASS"
        }
      ]
    }
  ],
  "proof_run_checks": {
    "no_external_sends": true,
    "no_unexpected_egress": true
  },
  "determinism_checks": {
    "stable_manifest": true,
    "no_duplicate_deliveries": true
  }
}
```

### 6. Output Validators
**Location:** `tests/e2e/output_validators/`  
**Status:** ⏳ PENDING

Validators for each format:
- `pdf_validator.py`
- `pptx_validator.py`
- `docx_validator.py`
- `csv_validator.py`
- `zip_validator.py`
- `html_validator.py`

### 7. Proof-Run Ledger
**Location:** `aicmo/safety/proof_run_ledger.py`  
**Status:** ⏳ PENDING

Records all attempted external sends for audit.

### 8. Network Egress Lock
**Location:** `aicmo/safety/egress_lock.py`  
**Status:** ⏳ PENDING

Deny-by-default HTTP egress with allowlist.

### 9. Delivery Gate
**Location:** `aicmo/delivery/gate.py`  
**Status:** ⏳ PENDING

Blocks delivery if validation status ≠ PASS.

### 10. Playwright Test Suite
**Location:** `tests/playwright/e2e_strict/`  
**Status:** ⏳ PENDING

Test categories:
- Positive tests (all outputs valid)
- Negative tests (must fail correctly)
- Determinism tests (idempotency)
- Concurrency tests (isolation)
- Auth tests (tenant boundaries)
- Performance tests (budgets)

## Test Execution

### Test Categories

#### 1. Positive Tests
Verify all valid outputs pass validation and can be delivered.

```bash
npm run test:e2e:positive
```

#### 2. Negative Tests
Verify invalid outputs fail validation and block delivery.

```bash
npm run test:e2e:negative
```

Tests:
- Placeholders present → FAIL
- Required sections missing → FAIL
- Forbidden phrases → FAIL
- ZIP path traversal → FAIL
- Validation FAIL attempts delivery → BLOCKED
- Proof-run attempts external send → FAIL
- Cross-tenant access → DENIED

#### 3. Determinism Tests
Verify same inputs produce stable outputs.

```bash
npm run test:e2e:determinism
```

#### 4. Concurrency Tests
Verify multiple clients don't interfere.

```bash
npm run test:e2e:concurrency
```

#### 5. Auth Tests
Verify tenant isolation.

```bash
npm run test:e2e:auth
```

#### 6. Performance Tests
Verify budgets are met.

```bash
npm run test:e2e:performance
```

### Full Suite

```bash
npm run test:e2e:strict
```

This runs all test categories and must be GREEN before merge.

## CI Integration

### Pre-Merge Gate

```yaml
# .github/workflows/e2e-gate.yml
name: E2E Client Output Gate

on: [pull_request]

jobs:
  e2e-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up environment
        run: ./scripts/setup_e2e_env.sh
      - name: Run E2E gate
        run: ./scripts/ci_e2e_gate.sh
      - name: Upload artifacts on failure
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-failure-artifacts
          path: |
            artifacts/e2e/
            test-results/
            playwright-report/
```

### Pass Criteria

CI passes only if:
- ✅ All Playwright tests pass
- ✅ All validation reports show PASS
- ✅ No manifest mismatches
- ✅ No egress violations
- ✅ Determinism tests pass
- ✅ Concurrency tests pass
- ✅ No external sends in proof-run
- ✅ Performance budgets met

## GREEN Definition

The suite is GREEN only if **ALL** of the following are true:

1. ✅ Every client-facing output is inventoried
2. ✅ Every artifact has a contract
3. ✅ Every artifact is validated
4. ✅ Every validation report is PASS
5. ✅ No placeholders exist
6. ✅ No forbidden phrases exist
7. ✅ No delivery bypasses validation
8. ✅ No external sends occur in proof-run
9. ✅ Reruns are deterministic
10. ✅ Concurrency is safe
11. ✅ Tenants are isolated
12. ✅ Performance budgets are met
13. ✅ All evidence artifacts exist

**Anything less is a FAIL.**

## Implementation Roadmap

### Phase 1: Foundation (Days 1-2)
- [x] Output inventory
- [x] Contract definitions
- [ ] Section map generator
- [ ] Artifact manifest
- [ ] Validation report schema

### Phase 2: Validators (Days 3-4)
- [ ] PDF validator
- [ ] PPTX validator
- [ ] DOCX validator
- [ ] CSV validator
- [ ] ZIP validator (recursive)
- [ ] HTML validator

### Phase 3: Safety (Days 5-6)
- [ ] Proof-run ledger
- [ ] Network egress lock
- [ ] Delivery gate enforcement

### Phase 4: Tests (Days 7-9)
- [ ] Positive tests
- [ ] Negative tests
- [ ] Determinism tests
- [ ] Concurrency tests
- [ ] Auth/tenant tests
- [ ] Performance tests

### Phase 5: CI (Day 10)
- [ ] CI workflow
- [ ] Artifact preservation
- [ ] Gate enforcement
- [ ] Documentation finalization

## Debugging

### Check Validation Status

```bash
# View latest validation report
cat artifacts/e2e/latest/validation_report.json | jq

# Check for failures
cat artifacts/e2e/latest/validation_report.json | jq '.artifacts[] | select(.status != "PASS")'
```

### Check Proof-Run Ledger

```bash
# Verify no external sends
cat artifacts/e2e/latest/proof_run_ledger.json | jq '.external_sends'
# Should be []
```

### Check Manifest

```bash
# View artifact manifest
cat artifacts/e2e/latest/manifest.json | jq

# Compare with downloaded files
ls artifacts/e2e/latest/
```

## Support

For questions or issues:
1. Check this document
2. Review [docs/e2e_client_output_inventory.md](e2e_client_output_inventory.md)
3. Review test output in `test-results/`
4. Review validation reports in `artifacts/e2e/*/validation_report.json`

## Version History

- **1.0.0** (2025-12-15): Initial implementation
