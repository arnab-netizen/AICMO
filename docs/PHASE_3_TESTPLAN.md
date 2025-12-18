1. Test Inventory

Exact Phase 3 test files and what each covers:

- `tests/test_artifact_contracts.py` — Verifies artifact contract enforcement, required fields, immutability checks, and checksum presence.
- `tests/test_artifact_optimistic_locking.py` — Verifies `ArtifactStore.put` optimistic-lock behavior, `expected_version` semantics, and `ConflictError` raising.
- `tests/test_schema_compatibility.py` — Verifies schema compatibility rules and `IncompatibleSchemaError` behavior for incompatible/unknown schema versions.
- `tests/test_api_contracts.py` — Verifies API request/response shape for `GenerateRequest/Response`, `ExportRequest/Response`, and `ErrorResponse`.
- `tests/test_client_ready.py` — Verifies `is_client_ready` logic for required artifacts, `passes_semantic_qc`, and `ProjectState` checks.

2. Negative Tests

Explicit failure modes that MUST be covered by tests (and must be included in the Phase 3 test inventory):

- Missing field: attempts to create or put an artifact missing a required field must fail validation.
- Mutation attempt: attempts to mutate an immutable field of a stored artifact (e.g., `content`, `checksum`, `schema_version`, `input_artifact_ids`) must not silently succeed; tests must detect that stored versions remain unchanged.
- Optimistic lock conflict: two concurrent writers using stale `expected_version` must cause `ConflictError` and the caller must detect conflict.
- Schema incompatibility: consumer encountering a breaking/unknown major `schema_version` must raise `IncompatibleSchemaError` (and API must map to `ErrorResponse` with `SCHEMA_INCOMPATIBLE`).
- Missing prereqs for client ready: `is_client_ready` must return `False` when any required artifact is missing, when `quality_contract.passes_semantic_qc` is `False`, or when `ProjectState` is not `QC_APPROVED`.

3. Commands

Exact commands to reproduce Phase 3 verification and test runs:

- Run Phase 3 verification (make target):

```bash
make verify-phase-3
```

- Run Phase 3 tests directly via pytest (captures same tests used by `verify-phase-3`):

```bash
pytest -q \
  tests/test_artifact_contracts.py \
  tests/test_artifact_optimistic_locking.py \
  tests/test_schema_compatibility.py \
  tests/test_api_contracts.py \
  tests/test_client_ready.py
```

- Compile-only check used in evidence collection:

```bash
python -m py_compile \
  aicmo/domain/artifacts.py \
  aicmo/ui/persistence/artifact_store.py \
  aicmo/api/schemas.py \
  aicmo/core/compat.py \
  aicmo/core/client_ready.py \
  aicmo/tools/verify_phase.py
```

4. Warning Handling Policy

- All warnings emitted during evidence generation (compile, smoke imports, pytest, verifier) MUST be captured in `audit_artifacts/phase_3/test_output.txt` and `audit_artifacts/phase_3/verify_output.txt` as part of the evidence pack.
- Benign warnings (for example, pytest config warnings) must be explicitly documented in `audit_artifacts/phase_3/warnings.md` with a clear explanation and justification for why they are acceptable for Phase 3 exit criteria.
- Deprecation or maintenance warnings that indicate code will break in the near future (e.g., Pydantic deprecation usage) MUST be fixed prior to the next phase. For Phase 3, any deprecation warnings observed in the verifier have to be remediated in the verifier (and the fix recorded) before final sign-off. The verifier must not silently emit deprecation warnings without remediation.

