import asyncio
from typing import List
from httpx import AsyncClient, ASGITransport
from backend.app import app


async def main() -> int:
    version_paths: List[str] = []
    for route in app.routes:
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
                data = r.json()
                # Require at least a couple of useful fields without being too strict
                has_name = any(k in data for k in ("name", "module", "service"))
                has_ver = any(k in data for k in ("version", "git", "build"))
                ok &= has_name and has_ver
    print("RESULT:", "OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
