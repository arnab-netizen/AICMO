from __future__ import annotations

import os
import pytest
from fastapi import HTTPException
from backend.security import require_admin, admin_token_enabled


def test_guard_allows_when_unset(monkeypatch):
    monkeypatch.delenv("ADMIN_TOKEN", raising=False)
    assert admin_token_enabled() is False
    # No exception should be raised
    require_admin(x_admin_token=None)


def test_guard_blocks_when_set_and_header_missing(monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "s3cr3t")
    with pytest.raises(HTTPException) as exc:
        require_admin(x_admin_token=None)
    assert exc.value.status_code == 401


def test_guard_blocks_when_set_and_header_wrong(monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "s3cr3t")
    with pytest.raises(HTTPException) as exc:
        require_admin(x_admin_token="nope")
    assert exc.value.status_code == 401


def test_guard_allows_when_set_and_header_correct(monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "s3cr3t")
    # No exception should be raised
    require_admin(x_admin_token="s3cr3t")
