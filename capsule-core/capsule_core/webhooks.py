from __future__ import annotations
from typing import Any, Dict
import anyio
import httpx


async def send_webhook(
    url: str, payload: Dict[str, Any], retries: int = 3, timeout: float = 10.0
) -> None:
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
