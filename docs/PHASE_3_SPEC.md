1. Purpose

Phase 3 objective: implement and freeze artifact contracts and delivery-surface guarantees necessary for immutable, versioned, traceable artifacts and safe downstream automation. Phase 3 covers:

- Artifact contracts (Pydantic domain model) and required invariants.
- Artifact immutability rules and listed immutable fields.
- Monotonic versioning of artifacts per (tenant_id, project_id, type).
- Schema compatibility policy and compatibility checker semantics.
- Optimistic locking semantics in the ArtifactStore (ConflictError semantics).
- API schema freeze for generation/export endpoints.
- Backend `is_client_ready` truth (authoritative, not UI-inferred).

This Phase defines the behavioral contract required for downstream automation and audit evidence (see Evidence Pack Requirements below).

2. Canonical Types and Imports

- `ProjectState` MUST be imported ONLY from `aicmo.domain.state_machine` throughout the codebase and docs.
- Duplicate `ProjectState` definitions are forbidden. Rationale: multiple enum definitions create ambiguous state identity and break phase gating and historical artifact invariants. The Phase‑2 patch canonicalized `ProjectState` into `aicmo.domain.state_machine` to eliminate drift; Phase 3 depends on that canonical source.

Artifact type/status policy:
- `ArtifactType` and `ArtifactStatus` are defined for Phase 3 usage in `aicmo.domain.artifacts`. Implementations should reference that single definition. If other enumerations exist in legacy modules, Phase 3 code MUST use `aicmo.domain.artifacts.ArtifactType` / `ArtifactStatus` and map/translate legacy values during migration.

3. Artifact Contract

The domain artifact model (as implemented in `aicmo/domain/artifacts.py`) requires the following fields and types:

- `id`: str
- `tenant_id`: str
- `project_id`: str
- `type`: `ArtifactType` (enum)
- `status`: `ArtifactStatus` (enum)
- `schema_version`: str
- `version`: int
- `produced_by`: str
- `produced_at`: str (ISO-8601 timestamp)
- `input_artifact_ids`: List[str]
- `state_at_creation`: `ProjectState`
- `trace_id`: str
- `created_by`: Literal["system","operator","client"]
- `checksum`: str
- `quality_contract`: object (structure `QualityContract` with fields: `artifact_type`, `required_depth`, `required_specificity`, `required_metrics`, `anti_generic_score`, `passes_semantic_qc`)
- `content`: Dict[str, Any]

Invariants (must be enforced by producers and validators):
- Immutability fields: once an artifact is stored as a version, the following fields are considered immutable and MUST NOT be altered for that stored version: `content`, `checksum`, `schema_version`, `input_artifact_ids` (as implemented by `Artifact.immutable_fields()`). Any attempt to mutate these fields for an existing version is a bug.
- Checksum definition: `checksum` is a deterministic digest (e.g., SHA256) over the canonical serialized `content` and any agreed metadata that must be covered (implementation-defined) so that identical artifact content yields identical checksum. Producers MUST compute and persist `checksum` at artifact creation.
- Version monotonicity: `version` is a monotonically increasing integer scoped to the tuple `(tenant_id, project_id, type)`. `version` starts at `1` for the first stored artifact and increments by 1 for each new stored version of that `(tenant_id, project_id, type)`.
- `trace_id` is required and MUST be carried through processing pipelines for observability and traceability.
- `tenant_id` and `project_id` are required non-empty identifiers; artifacts are always scoped by these two identifiers.

4. Artifact Store Semantics

Required store methods (store implementers must implement the following signatures/semantics):

- `put(artifact: Union[dict, DomainArtifact], expected_version: Optional[int] = None) -> Dict[str, Any]`
  - Persists a new artifact version rather than mutating an existing stored version.
  - If `expected_version` is provided, store MUST compare it to the latest stored version for `(tenant_id, project_id, type)` and raise `ConflictError` if they differ.
  - On success, `put` returns the stored artifact dict (including the assigned `version` and `id`).

- `get(tenant_id: str, artifact_id: str) -> Optional[Dict[str, Any]]`
  - Returns the artifact dict for the given `artifact_id` or `None` if not found.

- `list_by_project(tenant_id: str, project_id: str) -> List[Dict[str, Any]]`
  - Returns all artifact dicts for the given `(tenant_id, project_id)`.

- `latest(tenant_id: str, project_id: str, artifact_type: Union[str, ArtifactType]) -> Optional[Dict[str, Any]]`
  - Returns the latest artifact dict (highest `version`) for the given `(tenant_id, project_id, artifact_type)`, or `None`.

Optimistic locking rules:
- `expected_version` semantics: callers may supply the latest known version to avoid lost updates. If `expected_version` does not match the store's latest version for the tuple `(tenant_id, project_id, type)`, the store MUST raise `ConflictError`.
- `ConflictError` meaning: indicates the caller performed an operation based on a stale view of the artifact sequence; callers should re-fetch latest state, reconcile, and retry or report the conflict to the user.
- ErrorResponse mapping requirement: API layers MUST translate `ConflictError` into an `ErrorResponse` with `error_code` set to `CONFLICT` and an appropriate `message` field. This mapping is required so clients can programmatically handle concurrency failures.

5. Schema Compatibility Policy

`schema_version` rules and compatibility guarantees:
- The `schema_version` string is semantic: major.minor.patch (implementation may vary), and major version changes denote potential breaking changes.
- Allowed additive changes: adding optional fields with sane defaults is allowed and considered backward-compatible. Producers and consumers MUST agree on defaults or schema evolution rules.
- Breaking changes: removal of required fields, renaming required fields, or changing a required field's type are breaking changes and MUST be rejected by compatibility checks.
- Unknown major versions: if a consumer encounters an artifact with an unknown major `schema_version` that the consumer cannot safely parse, it MUST reject the artifact and surface an `IncompatibleSchemaError`.

`IncompatibleSchemaError` meaning:
- Raised when schema compatibility cannot be established for a requested operation. API layers must map this to an `ErrorResponse` with `error_code` set to `SCHEMA_INCOMPATIBLE` and an explanatory `message`.

6. API Contracts (Frozen)

The following Pydantic models are the frozen public API surface for Phase 3. Any change to these models must go through a formal Phase change.

- `GenerateRequest` fields:
  - `tenant_id` (str)
  - `project_id` (str)
  - `artifact_type` (str)
  - `idempotency_key` (Optional[str])
  - `trace_id` (Optional[str])
  - `requested_schema_version` (Optional[str])

- `GenerateResponse` fields:
  - `artifact_id` (str)
  - `status` (str)
  - `trace_id` (str)
  - `schema_version` (str)

- `ExportRequest` fields:
  - `tenant_id` (str)
  - `project_id` (str)
  - `idempotency_key` (str)
  - `trace_id` (str)
  - `bundle_schema_version` (str)

- `ExportResponse` fields:
  - `delivery_artifact_id` (str)
  - `trace_id` (str)
  - `bundle_schema_version` (str)

- `ErrorResponse` (only permissible error shape):
  - `error_code` (str)
  - `message` (str)
  - `details` (Optional[Dict[str, Any]])
  - `trace_id` (str)

Policy: `ErrorResponse` is the single allowed error payload for the frozen APIs. Handlers must serialize errors using this shape.

7. Client-Ready Truth

`is_client_ready(tenant_id, project_id, store)` is the authoritative backend-only check for whether an engagement is ready for client delivery. Rules:

- Required latest artifacts must exist (per Phase 3): `INTAKE`, `STRATEGY`, `CREATIVES` (artifact types are the canonical `ArtifactType` values). For each required artifact:
  - The latest artifact MUST exist (not `None`).
  - The artifact's `quality_contract.passes_semantic_qc` MUST be `True`.

- QC artifact status and project state:
  - The project `ProjectState` MUST be `QC_APPROVED` as represented by the canonical `aicmo.domain.state_machine.ProjectState` enum value. Implementations should check either the stored artifact's `state_at_creation` or the persisted project state representation.

- No UI inference: the `is_client_ready` truth is evaluated by backend state only. UI components may read this decision but must not infer readiness from local caches or heuristics.

8. Evidence Pack Requirements

Phase 3 is not complete without an audit-grade evidence pack present under `audit_artifacts/phase_3/`. Required files and what each proves:

- `diffstat.txt` — shows the git diffstat for Phase 3 changes (proves what files changed).
- `changed_files.txt` — list of changed file paths (proves scope of changes).
- `name_status.txt` — git name-status (proves adds/mods/deletes).
- `diff.patch` — full patch (proves exact code edits).
- `git_status.txt` — git workspace status at time of evidence collection.
- `commit_sha.txt` — HEAD commit used for the evidence pack.
- `pycompile.txt` — output of `python -m py_compile` for Phase 3 files (proves syntax correctness).
- `smoke_run_output.txt` — output of a smoke import run (proves modules import cleanly).
- `test_output.txt` — captured test run output including warnings (proves tests and records warnings).
- `verify_output.txt` — verifier output for Phase 3 (proves verifier PASS/FAIL).
- `schema_dump.json` — enumerates Artifact enums and API schema fields (proves contract surface).
- `warnings.md` — written explanation for any warnings observed during evidence generation (required for drift prevention).

Statement: Phase 3 is considered incomplete until the `audit_artifacts/phase_3/` directory contains the full set above and the verifier reports PASS.
