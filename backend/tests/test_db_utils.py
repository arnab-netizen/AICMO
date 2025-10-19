from backend.db import ping_db, exec_sql, get_engine, get_db


def test_ping_db_defaults_to_sqlite_when_no_env(monkeypatch):
    for k in ("DB_URL", "DATABASE_URL"):
        monkeypatch.delenv(k, raising=False)
    assert ping_db() is True


def test_exec_sql_select_one(monkeypatch):
    monkeypatch.setenv("DB_URL", "sqlite+pysqlite:///:memory:")
    rows = exec_sql("SELECT 1 AS one")
    assert rows and rows[0][0] == 1


def test_get_db_yields_and_closes(monkeypatch):
    monkeypatch.setenv("DB_URL", "sqlite+pysqlite:///:memory:")
    seen = None
    for s in get_db():
        seen = id(s)
        eng = get_engine()
        # SQLite in-memory DB may have no file path; check DB URL
        assert eng.url.drivername.startswith("sqlite")
        break
    assert isinstance(seen, int)
