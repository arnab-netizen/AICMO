from prometheus_client import Counter, Histogram

RUNS_TOTAL = Counter("capsule_runs_total", "Total runs", ["module", "status"])
RUNTIME_SECONDS = Histogram("capsule_runtime_seconds", "Run duration", ["module"])
