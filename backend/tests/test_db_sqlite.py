from backend.db import get_engine, get_db


def test_sqlite_engine_when_dburl_missing(monkeypatch):
    for k in ("DB_URL", "DATABASE_URL"):
        monkeypatch.delenv(k, raising=False)
    eng = get_engine()
    # Should be a valid SQLAlchemy Engine (likely sqlite memory)
    with eng.connect() as cx:
        cx.exec_driver_sql("SELECT 1")


def test_get_db_yields_session(monkeypatch):
    monkeypatch.setenv("DB_URL", "sqlite+pysqlite:///:memory:")
    sess = None
    for sess in get_db():
        # simple smoke: connection works
        sess.execute("SELECT 1")
        break
    assert sess is not None
