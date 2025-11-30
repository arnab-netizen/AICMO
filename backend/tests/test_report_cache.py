from __future__ import annotations

import time

from backend.utils.report_cache import ReportCache


def test_report_cache_basic_set_get():
    cache = ReportCache(max_size=10, ttl_seconds=60)

    assert cache.get("missing") is None

    cache.set("k1", {"foo": "bar"})
    assert cache.get("k1") == {"foo": "bar"}


def test_report_cache_ttl_expires():
    cache = ReportCache(max_size=10, ttl_seconds=0)

    cache.set("k1", {"foo": "bar"})
    time.sleep(0.01)
    assert cache.get("k1") is None


def test_report_cache_eviction():
    cache = ReportCache(max_size=2, ttl_seconds=60)

    cache.set("k1", 1)
    cache.set("k2", 2)
    cache.set("k3", 3)  # should evict oldest (k1)

    assert cache.get("k1") is None
    assert cache.get("k2") == 2
    assert cache.get("k3") == 3
