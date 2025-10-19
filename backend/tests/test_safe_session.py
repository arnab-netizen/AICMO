from backend.db import get_db


def test_safe_session_coerces_str_sql(monkeypatch):
    monkeypatch.setenv("DB_URL", "sqlite+pysqlite:///:memory:")
    for s in get_db():
        row = s.execute("SELECT 7 AS v").fetchone()
        assert row[0] == 7
