# DEPRECATED DIRECTORY — PHASE 1 CANONICALIZATION

This directory contains deprecated UI entrypoints and related files that are **FORBIDDEN** for import or use in any canonical code.

## Policy
- All files in this directory are **NOT CANONICAL**.
- It is **FORBIDDEN** to import from any file in this directory.
- Use `operator_v2.py` as the ONLY UI entrypoint.

## Reason
These files were moved here as part of Phase 1 canonicalization to eliminate ambiguity and enforce a single canonical UI entrypoint.

## Enforcement
- Tests and phase verification will FAIL if any code imports from this directory.
- This policy is enforced by `verify_phase.py` and the canonical entrypoint test suite.
