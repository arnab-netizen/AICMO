from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional, Tuple


class ReportCache:
    """
    Tiny in-memory cache for generated reports.

    Keyed by fingerprint (string), stores:
        - ts: float (monotonic time when stored)
        - value: arbitrary Python object (e.g. {"report_markdown": "...", ...})

    Not a distributed cache – just a local safety/perf booster.
    """

    def __init__(self, max_size: int = 128, ttl_seconds: int = 900) -> None:
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._store: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        now = time.monotonic()
        with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            ts, value = item
            if now - ts > self.ttl_seconds:
                # expired
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        now = time.monotonic()
        with self._lock:
            if len(self._store) >= self.max_size:
                # Evict oldest item
                oldest_key = min(self._store.items(), key=lambda kv: kv[1][0])[0]
                del self._store[oldest_key]
            self._store[key] = (now, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


# Singleton instance for the app to use
GLOBAL_REPORT_CACHE = ReportCache()
