from __future__ import annotations

import os
from fastapi import Header, HTTPException, status

ADMIN_HEADER_ALIAS = "x-admin-token"


def admin_token_enabled() -> bool:
    """True when ADMIN_TOKEN is set (non-empty)."""
    return bool(os.environ.get("ADMIN_TOKEN"))


def require_admin(
    x_admin_token: str | None = Header(default=None, alias=ADMIN_HEADER_ALIAS),
) -> None:
    """
    Optional admin guard.
    - If ADMIN_TOKEN is unset/empty → allow all.
    - If set → require header 'x-admin-token' to match exactly.
    """
    expected = os.environ.get("ADMIN_TOKEN")
    if not expected:
        # Guard disabled → allow
        return

    if x_admin_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )
