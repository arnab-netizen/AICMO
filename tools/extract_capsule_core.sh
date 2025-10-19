#!/usr/bin/env bash
set -euo pipefail

ROOT="${PWD}"
PKG_DIR="${ROOT}/capsule-core/capsule_core"
TESTS_DIR="${ROOT}/capsule-core/tests"
WF_DIR="${ROOT}/capsule-core/.github/workflows"

mkdir -p "${PKG_DIR}" "${TESTS_DIR}" "${WF_DIR}"

# --- Try to find existing files (best-effort) ---
find_run="$(rg -n --glob '!**/.venv/**' --glob '!**/node_modules/**' 'class RunRequest|class StatusResponse' || true)"
find_metrics="$(rg -n --glob '!**/.venv/**' --glob '!**/node_modules/**' 'class MetricsRegistry|Histogram|Counter' || true)"
find_logging="$(rg -n --glob '!**/.venv/**' --glob '!**/node_modules/**' 'structlog|get_logger' || true)"

echo "== Candidates =="
echo "run.py candidates:"
echo "${find_run:-<none>}"
echo
echo "metrics.py candidates:"
echo "${find_metrics:-<none>}"
echo
echo "logging.py candidates:"
echo "${find_logging:-<none>}"
echo

# Helper to copy first match if it exists, else write fallback
copy_first_match_or_fallback () {
  local search_out="$1"
  local fallback_path="$2"
  local dest_path="$3"

  if [ -n "${search_out}" ]; then
    # take first file path (before the colon)
    local src_file
    src_file="$(echo "${search_out}" | head -n1 | cut -d: -f1)"
    echo "Copying ${src_file} -> ${dest_path}"
    cp "${src_file}" "${dest_path}"
  else
    echo "No source found. Writing fallback: ${dest_path}"
    cat > "${dest_path}" < "${fallback_path}"
  fi
}

# --- Create temp fallbacks ---
TMPDIR="$(mktemp -d)"
cat > "${TMPDIR}/run.py" <<'PY'
from typing import Any, Dict, Optional, Literal
from pydantic import BaseModel, Field

TaskState = Literal["QUEUED", "RUNNING", "DONE", "ERROR", "CANCELLED"]

class RunRequest(BaseModel):
    project_id: str = Field(..., description="Project identifier")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Module-specific inputs")

class RunResponse(BaseModel):
    task_id: str
    accepted: bool = True

class StatusResponse(BaseModel):
    task_id: str
    state: TaskState
    score: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
PY

cat > "${TMPDIR}/metrics.py" <<'PY'
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
PY

cat > "${TMPDIR}/logging.py" <<'PY'
from __future__ import annotations
import logging
import sys
import structlog

def _configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(message)s",
        stream=sys.stdout,
    )
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

_configure_logging()

def get_logger(name: str = "capsule") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
PY

cat > "${TMPDIR}/webhooks.py" <<'PY'
from __future__ import annotations
from typing import Any, Dict
import anyio
import httpx

async def send_webhook(url: str, payload: Dict[str, Any], retries: int = 3, timeout: float = 10.0) -> None:
    last_exc: Exception | None = None
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(1, retries + 1):
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                await anyio.sleep(0.5 * attempt)
    if last_exc:
        raise last_exc
PY

# --- Write package metadata ---
cat > "${ROOT}/capsule-core/pyproject.toml" <<'TOML'
[build-system]
requires = ["hatchling>=1.25.0"]
build-backend = "hatchling.build"

[project]
name = "capsule-core"
version = "0.1.0"
description = "Shared run schemas, metrics, logging, and webhook helpers for AI-CMO capsules."
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [{name = "AI-CMO"}]
dependencies = ["pydantic>=2.7,<3", "httpx>=0.27,<0.28", "structlog>=24.1,<25", "anyio>=4"]

[tool.hatch.build.targets.wheel]
packages = ["capsule_core"]
TOML

cat > "${ROOT}/capsule-core/README.md" <<'MD'
# capsule-core
Shared types/helpers for AI-CMO capsules: run schemas, metrics, logging, webhooks.
MD

cat > "${PKG_DIR}/__init__.py" <<'PY'
__all__ = ["run", "metrics", "logging", "webhooks"]
PY

# --- Populate package files from existing code or fallbacks ---
copy_first_match_or_fallback "${find_run}"     "${TMPDIR}/run.py"     "${PKG_DIR}/run.py"
copy_first_match_or_fallback "${find_metrics}" "${TMPDIR}/metrics.py" "${PKG_DIR}/metrics.py"
copy_first_match_or_fallback "${find_logging}" "${TMPDIR}/logging.py" "${PKG_DIR}/logging.py"
cp "${TMPDIR}/webhooks.py" "${PKG_DIR}/webhooks.py"

# --- Minimal smoke test ---
cat > "${TESTS_DIR}/test_core_imports.py" <<'PY'
from capsule_core.run import RunRequest, RunResponse, StatusResponse
from capsule_core.metrics import get_registry
from capsule_core.logging import get_logger
from capsule_core.webhooks import send_webhook

def test_imports_and_basics():
    _ = RunRequest(project_id="p1", payload={})
    _ = RunResponse(task_id="t1")
    _ = StatusResponse(task_id="t1", state="QUEUED")
    reg = get_registry()
    reg.counter("jobs").inc()
    reg.histogram("latency").observe(0.01)
    log = get_logger("test")
    log.info("ok")
PY

echo "== capsule-core scaffolded at ${ROOT}/capsule-core =="
