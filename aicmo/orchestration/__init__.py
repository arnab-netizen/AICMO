"""
Autonomy Orchestration Layer (AOL) - Main daemon, queue, and lease management.

Public API:
- daemon.AOLDaemon: Main loop runner
- queue.ActionQueue: Action enqueue/dequeue
- lease.LeaseManager: Distributed lock
- adapters.social_adapter: POST_SOCIAL action handler
"""

__version__ = "1.0.0"
CONTRACT_VERSION = 1

__all__ = []

# Import models to register with SQLAlchemy Base
from aicmo.orchestration import models  # noqa: F401
