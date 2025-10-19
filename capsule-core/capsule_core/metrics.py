from __future__ import annotations
from typing import Dict, Tuple
import time
from contextlib import contextmanager


class Counter:
    def __init__(self) -> None:
        self.value = 0

    def inc(self, n: int = 1) -> None:
        self.value += n


class Histogram:
    def __init__(self) -> None:
        self.values = []

    @contextmanager
    def time(self):
        t0 = time.perf_counter()
        try:
            yield
        finally:
            self.observe(time.perf_counter() - t0)

    def observe(self, v: float) -> None:
        self.values.append(v)


class MetricsRegistry:
    def __init__(self, namespace: str = "capsule") -> None:
        self.ns = namespace
        self.counters: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], Counter] = {}
        self.hists: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], Histogram] = {}

    def counter(self, name: str, **labels: str) -> Counter:
        key = (f"{self.ns}_{name}", tuple(sorted(labels.items())))
        if key not in self.counters:
            self.counters[key] = Counter()
        return self.counters[key]

    def histogram(self, name: str, **labels: str) -> Histogram:
        key = (f"{self.ns}_{name}", tuple(sorted(labels.items())))
        if key not in self.hists:
            self.hists[key] = Histogram()
        return self.hists[key]


# singleton convenience
_registry = MetricsRegistry()


def get_registry(namespace: str | None = None) -> MetricsRegistry:
    return _registry if namespace is None else MetricsRegistry(namespace)
