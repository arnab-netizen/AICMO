# AICMO Architecture Guardrails

- backend/* = existing API behaviour. MUST keep working.
- aicmo/*   = new modular monolith:
  - domain/    = Pydantic models, enums
  - core/      = DB, config, workflow (state machine)
  - strategy/  = intake -> strategy docs
  - creatives/ = strategy -> creatives
  - delivery/  = projects, orchestrator, HTTP layer
  - gateways/  = ports & adapters (execution)
  - acquisition/ = Apollo, enrichment
  - cam/       = Client Acquisition Mode (lead finder + outreach)

Global rules for any changes:
1. Do NOT change public FastAPI route paths or request/response models under backend/routers/* unless explicitly instructed.
2. Do NOT delete or rename existing backend modules without explicit instruction.
3. Do NOT remove fields from existing DB models or migrations; only add new ones via new Alembic migrations.
4. New business logic goes under aicmo/* and is called via thin wrappers from existing code.
5. After each phase, run `make ci` (or pytest) and ensure all tests pass.
6. If tests fail, fix ONLY the new code, or add targeted tests; do NOT "simplify" or remove existing logic.
