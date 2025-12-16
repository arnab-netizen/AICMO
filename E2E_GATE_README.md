# E2E Client Output Gate - Complete Implementation

## Overview

The E2E Client Output Gate is a **non-negotiable** validation system that ensures all client-facing outputs are production-ready before delivery. If the Playwright suite is GREEN, AICMO is safe to deliver client-facing outputs in real usage.

## Quick Start

### 1. Start E2E Mode

```bash
./scripts/start_e2e_streamlit.sh
```

This sets all required environment variables and starts Streamlit in E2E mode with:
- Proof-run mode (no real sends)
- Network egress lock (deny-by-default)
- Deterministic seed for reproducibility
- Validation contracts loaded

### 2. Run E2E Tests

```bash
# Run all tests
npm run test:e2e:strict

# Run positive tests only
npx playwright test tests/playwright/e2e_strict/positive_tests.spec.ts

# Run negative tests only
npx playwright test tests/playwright/e2e_strict/negative_tests.spec.ts
```

### 3. Check Validation

```bash
./scripts/check_e2e_validation.sh
```

This verifies:
- ✅ Global status = PASS
- ✅ All artifacts = PASS
- ✅ No placeholders
- ✅ No forbidden phrases
- ✅ No external sends in proof-run
- ✅ No egress violations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Generator                              │
│  (Strategy, Brief, Campaign, Outreach, etc.)                 │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ├─► Section Map (source of truth)
                    │   - section_id, title, word_count
                    │   - content_hash (SHA256)
                    │   - Saved to: {artifact_dir}/section_maps/
                    │
                    ├─► Artifact Creation
                    │   - PDF, PPTX, DOCX, CSV, ZIP, HTML
                    │   - Saved to: {artifact_dir}/
                    │
                    └─► Manifest Generation
                        - Lists all artifacts
                        - SHA256 checksums
                        - Saved to: {artifact_dir}/manifest.json
                        
┌─────────────────────────────────────────────────────────────┐
│                    Validation Pipeline                        │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ├─► Structural Validator
                    │   - PDF: page count, metadata
                    │   - PPTX: slide count, speaker notes
                    │   - DOCX: paragraph count, tables
                    │   - CSV: column headers, row count
                    │   - ZIP: archive validity, path traversal
                    │   - HTML: character count, elements
                    │
                    ├─► Safety Validator
                    │   - Placeholder detection ({{...}})
                    │   - Forbidden phrase scanning (TODO, FIXME)
                    │   - Required string validation
                    │   - File size limits
                    │
                    ├─► Content Validator
                    │   - Section map validation
                    │   - Word count requirements
                    │   - Required sections present
                    │
                    └─► Validation Report
                        - Per-artifact status (PASS/FAIL)
                        - Global status (PASS/FAIL)
                        - Detailed issues list
                        - Saved to: {artifact_dir}/validation_report.json

┌─────────────────────────────────────────────────────────────┐
│                      Delivery Gate                            │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ├─► Check validation status
                    │   - If PASS: Allow delivery
                    │   - If FAIL: Block delivery
                    │
                    ├─► Check proof-run compliance
                    │   - No external sends
                    │   - No egress violations
                    │
                    └─► Enforcement
                        - Blocks UI delivery button if FAIL
                        - Raises DeliveryBlockedError if bypassed
                        - Logs all attempts to audit trail
```

## Components

### 1. Output Inventory

**Location**: [docs/e2e_client_output_inventory.md](docs/e2e_client_output_inventory.md)

Complete enumeration of all 7 client-facing outputs:
- Marketing Strategy Report (PDF)
- Marketing Strategy Presentation (PPTX)
- Marketing Brief (DOCX)
- Lead Export (CSV)
- Outreach Email Preview (HTML)
- Campaign Report (TXT)
- Complete Deliverable Package (ZIP)

### 2. Validation Contracts

**Location**: [tests/e2e/specs/client_outputs.contract.json](tests/e2e/specs/client_outputs.contract.json)

Machine-readable contracts defining validation rules for each output:
- Required sections
- Required strings
- Forbidden patterns (placeholders, TODO markers)
- Min/max word counts
- Min/max page/slide counts
- Max file size
- Dynamic allowlist patterns

### 3. Section Map Generator

**Location**: [aicmo/validation/section_map.py](aicmo/validation/section_map.py)

Creates structured section maps at generation time:
```python
from aicmo.validation import SectionMapGenerator

generator = SectionMapGenerator()
section_map = generator.create_from_dict(
    document_id='marketing_strategy_report_001',
    document_type='marketing_strategy_report_pdf',
    sections={
        'Executive Summary': executive_summary_text,
        'Market Analysis': market_analysis_text,
        # ... more sections
    }
)
section_map.save(f'{artifact_dir}/section_maps/{document_id}.json')
```

### 4. Artifact Manifest

**Location**: [aicmo/validation/manifest.py](aicmo/validation/manifest.py)

Tracks all artifacts with checksums:
```python
from aicmo.validation import ManifestGenerator

generator = ManifestGenerator()
manifest = generator.create_from_directory(
    artifact_dir='/path/to/artifacts',
    run_id='e2e-run-001',
    client_id='client-123'
)
manifest.save(f'{artifact_dir}/manifest.json')
```

### 5. Output Validators

**Location**: [tests/e2e/output_validators/](tests/e2e/output_validators/)

Format-specific validators:
- **PDFValidator**: Page count, metadata, text extraction (PyPDF2)
- **PPTXValidator**: Slide count, speaker notes (python-pptx)
- **DOCXValidator**: Paragraph count, tables (python-docx)
- **CSVValidator**: Column headers, row count (csv)
- **ZIPValidator**: Archive validity, recursive validation (zipfile)
- **HTMLValidator**: Character count, element presence (html.parser)

Usage:
```python
from tests.e2e.output_validators import get_validator
from aicmo.validation import OutputValidator

# Load contract
validator = OutputValidator('contracts.json')

# Validate artifact
result = validator.validate_artifact(
    artifact_id='marketing_strategy_report_pdf',
    filepath='/path/to/report.pdf',
    section_map=section_map
)

print(result.status)  # PASS or FAIL
print(result.issues)  # List of issues if FAIL
```

### 6. Proof-Run Ledger

**Location**: [aicmo/safety/proof_run_ledger.py](aicmo/safety/proof_run_ledger.py)

Tracks all send attempts:
```python
from aicmo.safety import record_send_attempt

if AICMO_PROOF_RUN:
    record_send_attempt('email', recipient, 'Campaign X', False, 'Proof-run mode')
else:
    send_email(recipient, body)
    record_send_attempt('email', recipient, 'Campaign X', True)
```

Verification:
```python
from aicmo.safety import get_ledger

ledger = get_ledger()
is_compliant, violations = ledger.verify_no_external_sends()

if not is_compliant:
    print(f"External sends detected: {violations}")
```

### 7. Network Egress Lock

**Location**: [aicmo/safety/egress_lock.py](aicmo/safety/egress_lock.py)

Deny-by-default HTTP egress:
```python
from aicmo.safety import check_egress_allowed, require_egress_allowed

# Check if URL is allowed
if check_egress_allowed('https://external-api.com/v1/data'):
    response = requests.post(url, data=payload)

# Or require (raises if blocked)
require_egress_allowed('https://external-api.com/v1/data', 'SendGrid API call')
response = requests.post(url, data=payload)
```

Patch at application startup:
```python
from aicmo.safety import EgressLock

lock = EgressLock()
lock.patch_http_libraries()  # Monkey-patches requests, urllib, httpx
```

### 8. Validation Orchestrator

**Location**: [aicmo/validation/validator.py](aicmo/validation/validator.py)

Orchestrates full validation pipeline:
```python
from aicmo.validation import OutputValidator

validator = OutputValidator('contracts.json')

# Validate single artifact
result = validator.validate_artifact(
    artifact_id='marketing_strategy_report_pdf',
    filepath='/path/to/report.pdf',
    section_map=section_map
)

# Validate entire manifest
validation_report = validator.validate_manifest(manifest)

print(validation_report.global_status)  # PASS or FAIL
print(validation_report.is_pass)  # True or False

if not validation_report.is_pass:
    print(validation_report.get_failure_summary())
```

### 9. Delivery Gate

**Location**: [aicmo/delivery/gate.py](aicmo/delivery/gate.py)

Blocks delivery on validation failure:
```python
from aicmo.delivery import check_delivery_allowed, block_delivery

# Check if delivery is allowed
if check_delivery_allowed(validation_report):
    deliver_to_client(artifacts)
else:
    show_error("Delivery blocked - validation failed")

# Or block with exception (preferred)
try:
    block_delivery(validation_report)
    deliver_to_client(artifacts)
except DeliveryBlockedError as e:
    show_error(str(e))
```

### 10. Playwright Tests

**Location**: [tests/playwright/e2e_strict/](tests/playwright/e2e_strict/)

Comprehensive test suites:
- **positive_tests.spec.ts**: Valid outputs pass validation
- **negative_tests.spec.ts**: Invalid outputs fail correctly

## Test Execution

### Positive Tests (10 tests)

1. PDF Report - Marketing Strategy Report
2. PPTX Deck - Marketing Strategy Presentation
3. DOCX Brief - Marketing Brief
4. CSV Export - Lead List
5. HTML Email Preview - Outreach Email
6. ZIP Archive - Complete Deliverable
7. Campaign Report - Text Format
8. Global Validation - All Outputs PASS
9. Delivery Gate - Allow Delivery on PASS
10. Manifest Integrity - Checksums Match

### Negative Tests (12 tests)

1. Placeholder Detection - {{PLACEHOLDER}} in output
2. Missing Required Section - Executive Summary
3. Forbidden Phrase - "TODO" in output
4. Word Count Below Threshold
5. Invalid File Structure - Corrupted PDF
6. External Send in Proof-Run - Email Blocked
7. Network Egress Blocked - External API Call
8. Delivery Gate - Block Delivery on FAIL
9. CSV Invalid Structure - Missing Required Columns
10. ZIP Path Traversal - Malicious Paths Blocked
11. Multiple Failures - Cumulative FAIL Status
12. File Size Exceeded - MAX_FILE_SIZE Enforcement

## CI Integration

The E2E gate runs automatically on all PRs via GitHub Actions:

**Workflow**: [.github/workflows/e2e-gate.yml](.github/workflows/e2e-gate.yml)

**Triggers**:
- Pull requests to `main` or `develop`
- Pushes to `main` or `develop`
- Manual workflow dispatch

**Steps**:
1. Set up Python 3.11 and Node.js 20
2. Install dependencies (Python, Node, Playwright)
3. Run E2E gate script
4. Upload validation reports
5. Check gate status
6. Block merge if gate is RED

**Artifacts** (retained for 7 days):
- `e2e-validation-report`: validation_report.json, manifest.json, proof_run_ledger.json
- `playwright-results`: Test results and screenshots
- `failed-artifacts` (on failure): All generated outputs for debugging

## Definition of GREEN

The E2E gate is **GREEN** if and only if ALL of the following are true:

1. ✅ Every client-facing output is inventoried
2. ✅ Every artifact has a contract
3. ✅ Every artifact is validated
4. ✅ Every validation report is PASS
5. ✅ No placeholders exist ({{...}})
6. ✅ No forbidden phrases exist (TODO, FIXME, etc.)
7. ✅ No delivery bypasses validation
8. ✅ No external sends occur in proof-run
9. ✅ Reruns are deterministic (same seed → same checksums OR controlled versioning)
10. ✅ Concurrency is safe (multiple clients don't interfere)
11. ✅ Tenants are isolated (no data leakage)
12. ✅ Performance budgets are met (generation time < thresholds)
13. ✅ All evidence artifacts exist (section maps, manifests, validation reports)

**Anything less than this guarantee is a failure.**

## Environment Variables

### Required for E2E Mode

```bash
# Enable E2E mode
export AICMO_E2E_MODE=1
export AICMO_E2E_DIAGNOSTICS=1

# Force proof-run (no real sends)
export AICMO_PROOF_RUN=1

# Deterministic seed
export AICMO_TEST_SEED=e2e-deterministic-seed-2025

# Persistence mode (db only)
export AICMO_PERSISTENCE_MODE=db

# Artifact directory
export AICMO_E2E_ARTIFACT_DIR=/workspaces/AICMO/artifacts/e2e

# Network egress allowlist (comma-separated regex patterns)
export AICMO_EGRESS_ALLOWLIST="^https?://127\.0\.0\.1,^https?://localhost"

# Validation contracts
export AICMO_CONTRACTS_PATH=/workspaces/AICMO/tests/e2e/specs/client_outputs.contract.json
```

## Debugging

### Check Validation Report

```bash
cat artifacts/e2e/validation_report.json | jq '.'
```

Key fields:
- `.global_status`: "PASS" or "FAIL"
- `.artifacts[].status`: Per-artifact status
- `.artifacts[].issues`: List of failure reasons
- `.proof_run_checks.no_external_sends`: Should be `true`
- `.proof_run_checks.egress_violations`: Should be empty array

### Check Proof-Run Ledger

```bash
cat artifacts/e2e/proof_run_ledger.json | jq '.'
```

Key fields:
- `.proof_run_mode`: Should be `true`
- `.external_sends`: Should be empty array
- `.blocked_sends`: List of blocked attempts
- `.all_attempts`: Complete audit trail

### Check Manifest

```bash
cat artifacts/e2e/manifest.json | jq '.'
```

Key fields:
- `.artifacts[]`: List of all artifacts
- `.artifacts[].checksum_sha256`: SHA256 checksum for integrity

### Check Section Maps

```bash
ls -la artifacts/e2e/section_maps/
cat artifacts/e2e/section_maps/marketing_strategy_report_001.json | jq '.'
```

## Implementation Status

### ✅ Completed (Phase 1-3)

- [x] Output inventory documentation
- [x] Machine-readable contracts (JSON)
- [x] E2E gate comprehensive guide
- [x] Section map generator
- [x] Artifact manifest generator
- [x] Validation framework orchestration
- [x] 7 format-specific validators
- [x] Proof-run ledger
- [x] Network egress lock
- [x] Delivery gate
- [x] Playwright positive tests (10 tests)
- [x] Playwright negative tests (12 tests)
- [x] Helper scripts (start, check, CI)
- [x] CI workflow configuration

### ⏳ Pending (Phase 4-5)

- [ ] Integration with generators (section map creation)
- [ ] Integration with delivery pipeline (gate enforcement)
- [ ] Database schema for persistence
- [ ] Determinism tests (rerun comparison)
- [ ] Concurrency tests (multi-client isolation)
- [ ] Auth/tenant isolation tests
- [ ] Performance budget tests
- [ ] Streamlit UI E2E diagnostics panel

## Next Steps

### 1. Integrate Section Maps into Generators

**Example** (strategy_generator.py):
```python
from aicmo.validation import SectionMapGenerator

def generate_strategy_report(client_id, params):
    # ... generate sections ...
    
    # Create section map
    generator = SectionMapGenerator()
    section_map = generator.create_from_dict(
        document_id=f'strategy_report_{client_id}_{timestamp}',
        document_type='marketing_strategy_report_pdf',
        sections={
            'Executive Summary': executive_summary,
            'Market Analysis': market_analysis,
            # ... all sections
        }
    )
    
    # Save section map
    section_map.save(f'{artifact_dir}/section_maps/{document_id}.json')
    
    # Generate PDF
    pdf_path = create_pdf(sections)
    
    return pdf_path, section_map
```

### 2. Integrate Delivery Gate into UI

**Example** (streamlit_app.py):
```python
from aicmo.delivery import check_delivery_allowed
from aicmo.validation import OutputValidator

# After generation
validator = OutputValidator(contracts_path)
validation_report = validator.validate_manifest(manifest)

# Show status in UI
if validation_report.is_pass:
    st.success("✅ All outputs validated - ready for delivery")
    if st.button("Deliver to Client"):
        try:
            block_delivery(validation_report)
            deliver_to_client(artifacts)
            st.success("Delivered successfully!")
        except DeliveryBlockedError as e:
            st.error(f"Delivery blocked: {e}")
else:
    st.error("❌ Validation failed - cannot deliver")
    st.write(validation_report.get_failure_summary())
```

### 3. Add E2E Diagnostics Panel

Add tab in Streamlit UI showing:
- Current E2E mode status
- Validation report summary
- Proof-run ledger
- Quick validation checks
- Reset button for clean runs

### 4. Run Determinism Tests

```bash
# Run same workflow twice
./scripts/ci_e2e_gate.sh
mv artifacts/e2e artifacts/e2e_run1

./scripts/ci_e2e_gate.sh
mv artifacts/e2e artifacts/e2e_run2

# Compare checksums
diff artifacts/e2e_run1/manifest.json artifacts/e2e_run2/manifest.json
```

## Support

For questions or issues:
1. Check validation report: `./scripts/check_e2e_validation.sh`
2. Review generated artifacts: `ls -la artifacts/e2e/`
3. Check test results: `npx playwright show-report`
4. Review implementation guide: [docs/e2e_strict_client_output_gate.md](docs/e2e_strict_client_output_gate.md)

## License

Part of the AICMO project. See main LICENSE file.
