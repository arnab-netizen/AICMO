"""Simple persistence adapter for Intake data.

Implements two modes controlled by env `AICMO_PERSISTENCE_MODE`:
- inmemory: store in-process dicts
- db: attempt to use existing backend DB layer (not implemented here)

This adapter is intentionally small and explicit so the UI code can
call create_client/create_engagement without guessing IDs.
"""
from __future__ import annotations

import os
import uuid
from typing import Dict, Any


class IntakeStore:
    def __init__(self, mode: str = "inmemory"):
        self.mode = mode or "inmemory"
        if self.mode == "inmemory":
            # simple module-level in-memory store
            if not hasattr(_inmemory_store, "clients"):
                _inmemory_store.clients = {}
                _inmemory_store.engagements = {}

    def create_client(self, profile: Dict[str, Any]) -> str:
        if self.mode == "inmemory":
            client_id = str(uuid.uuid4())
            _inmemory_store.clients[client_id] = dict(profile)
            return client_id
        # db mode not implemented: explicit fail to avoid silent DB claims
        raise RuntimeError("DB persistence mode not implemented in IntakeStore")

    def create_engagement(self, client_id: str, engagement: Dict[str, Any]) -> str:
        if self.mode == "inmemory":
            eid = str(uuid.uuid4())
            _inmemory_store.engagements[eid] = {"client_id": client_id, **engagement}
            return eid
        raise RuntimeError("DB persistence mode not implemented in IntakeStore")


# a tiny holder object to keep global dicts on the module
class _inmemory_store:  # pragma: no cover - simple container
    clients = {}
    engagements = {}
