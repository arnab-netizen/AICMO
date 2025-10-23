import asyncio
from typing import List
import os
import sys
from pathlib import Path

# If this repository contains a top-level `capsule-core` package directory,
# make it importable automatically. This lets CI run `python -m backend.tools.smoke_versions`
# without needing to set PYTHONPATH manually.
try:
    repo_root = Path(__file__).resolve().parents[2]
    capsule_core_dir = repo_root / "capsule-core"
    if capsule_core_dir.exists() and str(capsule_core_dir) not in sys.path:
        sys.path.insert(0, str(capsule_core_dir))
except Exception:
    # Be conservative: if anything goes wrong here, fall back to default imports
    pass


async def main() -> int:
    # Lazy import app to avoid optional dependency crashes during CI/quick runs.
    try:
        if os.environ.get("SITEGEN_ENABLED", "1") == "0":
            print(
                "SITEGEN_ENABLED=0 -> skipping SiteGen-heavy imports; attempting to import minimal app"
            )
        import importlib
        from httpx import AsyncClient, ASGITransport

        app = importlib.import_module("backend.app").app
    except ModuleNotFoundError as mnf:
        # Try to be resilient in CI: if small optional deps are missing (e.g., structlog or httpx),
        # attempt a best-effort pip install and retry once.
        missing = mnf.name
        print("APP_IMPORT_MISSING:", missing)
        try:
            import subprocess

            print(f"Attempting to pip install missing package: {missing}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", missing])
        except Exception as pip_e:
            print("pip install attempt failed:", pip_e)
            print("APP_IMPORT_ERROR:", repr(mnf))
            return 3
        # Retry imports once
        try:
            import importlib
            from httpx import AsyncClient, ASGITransport

            app = importlib.import_module("backend.app").app
        except Exception as e:
            print("APP_IMPORT_ERROR after pip retry:", repr(e))
            return 3
    except Exception as e:
        print("APP_IMPORT_ERROR:", repr(e))
        return 3

    version_paths: List[str] = []
    for route in getattr(app, "routes", []):
        # Be defensive; some routes (starlette) don't have all attrs
        try:
            path = getattr(route, "path", "")
            methods = getattr(route, "methods", set())
        except Exception:
            continue
        if isinstance(path, str) and path.endswith("/version") and ("GET" in methods):
            version_paths.append(path)

    if not version_paths:
        print("No /version endpoints found.")
        return 2

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ok = True
        for p in version_paths:
            r = await client.get(p)
            print(p, r.status_code, r.text)
            if r.status_code != 200:
                ok = False
            else:
                try:
                    data = r.json()
                except Exception:
                    data = {}
                # Require at least a couple of useful fields without being too strict
                has_name = any(k in data for k in ("name", "module", "service"))
                has_ver = any(k in data for k in ("version", "git", "build"))
                ok &= has_name and has_ver
    print("RESULT:", "OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
