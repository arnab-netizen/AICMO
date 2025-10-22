from backend.db import get_db


def test_health_db_503_when_operation_fails(monkeypatch, client):
    class BoomSession:
        def execute(self, *a, **kw):
            raise RuntimeError("db op failed intentionally")

        def close(self):
            pass

    def broken_db():
        yield BoomSession()

    app = client.app
    app.dependency_overrides[get_db] = broken_db
    try:
        r = client.get("/health/db")
        assert r.status_code == 503
        body = r.json()
        assert body.get("status") == "error"
        assert "failed" in (body.get("detail") or "").lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_health_db_500_when_engine_unavailable(monkeypatch, client):
    def raising_get_db():
        raise RuntimeError("engine unavailable")

    app = client.app
    app.dependency_overrides[get_db] = raising_get_db
    try:
        r = client.get("/health/db")
        assert r.status_code == 500
        body = r.json()
        assert body.get("status") == "error"
        assert "unavailable" in (body.get("detail") or "").lower()
    finally:
        app.dependency_overrides.pop(get_db, None)
