from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from backend.security import require_admin


def make_app():
    app = FastAPI()

    @app.get("/secure", dependencies=[Depends(require_admin)])
    def secure():
        return {"ok": True}

    return app


def test_secure_route_allows_when_unset(monkeypatch):
    monkeypatch.delenv("ADMIN_TOKEN", raising=False)
    client = TestClient(make_app())
    r = client.get("/secure")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_secure_route_blocks_when_set_and_missing(monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "token-123")
    client = TestClient(make_app())
    r = client.get("/secure")
    assert r.status_code == 401


def test_secure_route_allows_when_set_and_correct(monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "token-123")
    client = TestClient(make_app())
    r = client.get("/secure", headers={"x-admin-token": "token-123"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}
