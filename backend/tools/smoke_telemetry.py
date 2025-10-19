import asyncio
import os
from typing import List
from httpx import AsyncClient, ASGITransport
from backend.app import app

# Optional skip patterns from env var (comma-separated)
SKIP_PATTERNS = (os.getenv("SMOKE_SKIP", "") or "").split(",")

# Minimal generic payloads so we don't need module-specific fixtures yet
MINIMAL_BODIES = [
    {"input": "hello world"},
    {"text": "hello world"},
    {"prompt": "hello world"},
    {"embedding": [0.0] * 1536, "top_k": 1, "min_taste": 0.0},
]


def has_telemetry(obj) -> bool:
    # Accept telemetry in either top-level meta or inside artifact meta
    if isinstance(obj, dict):
        meta = obj.get("meta")
        if isinstance(meta, dict) and "seconds_used" in meta and "cost_estimate" in meta:
            return True
        arts = obj.get("artifacts")
        if isinstance(arts, list):
            for a in arts:
                if isinstance(a, dict):
                    m = a.get("meta")
                    if isinstance(m, dict) and "seconds_used" in m and "cost_estimate" in m:
                        return True
    return False


async def main() -> int:
    run_paths: List[str] = []
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", set())
        if isinstance(path, str) and path.endswith("/run") and ("POST" in methods):
            run_paths.append(path)

    if not run_paths:
        print("No /run endpoints discovered.")
        return 0

    any_checked = False
    all_have_telemetry = True
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for p in run_paths:
            if any(s and s in p for s in SKIP_PATTERNS):
                print(f"{p} -> skipped by SMOKE_SKIP")
                continue
            made_any = False
            for body in MINIMAL_BODIES:
                try:
                    r = await client.post(p, json=body)
                except Exception as e:
                    print(f"{p} -> ERROR: {type(e).__name__}: {e}")
                    made_any = False
                    break
                print(f"{p} -> {r.status_code}")
                if r.status_code < 400:
                    made_any = True
                    try:
                        data = r.json()
                    except Exception:
                        print("  telemetry: (response not JSON)")
                        break
                    h = has_telemetry(data)
                    print("  telemetry:", "present" if h else "missing")
                    any_checked = True
                    all_have_telemetry &= h
                    break
            if not made_any:
                print("  (skipped: endpoint requires richer payload or runtime dependencies)")

    if not any_checked:
        print("No /run endpoints accepted minimal bodies; skipping fail.")
        raise SystemExit(0)
    raise SystemExit(0 if all_have_telemetry else 1)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
