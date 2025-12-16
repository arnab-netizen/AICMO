"""
Campaign Orchestrator - Fast Revenue Marketing Engine Phase 2.

Continuous campaign execution loop that:
- Picks eligible leads
- Chooses messages
- Dispatches distribution jobs
- Records outcomes
- Advances lead state

Production-safe with:
- Kill switch enforcement
- Pause/resume controls
- Idempotency guarantees
- DNC/suppression/unsubscribe enforcement
- Single-writer lease (concurrency safety)
- Per-lead transaction boundaries
"""

from aicmo.cam.orchestrator.models import (
    OrchestratorRunDB,
    UnsubscribeDB,
    SuppressionDB,
    RunStatus,
)

__all__ = [
    "OrchestratorRunDB",
    "UnsubscribeDB",
    "SuppressionDB",
    "RunStatus",
]
