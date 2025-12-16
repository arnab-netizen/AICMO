"""
Campaign Operations Layer - Operator Command Center

Provides campaign planning, calendar, task management, and reporting
for manual operator execution (no autonomous posting).

Safe, proof-mode defaults: operators execute actions manually on platforms
and mark completion in AICMO.
"""

__version__ = "0.1.0"
__all__ = [
    "models",
    "service",
    "schemas",
    "instructions",
    "actions",
    "wiring",
]
