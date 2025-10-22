import asyncio
from typing import List
import os


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
