from backend.db import exec_sql, get_db


def test_exec_sql_two_arg_returns_result(monkeypatch):
    monkeypatch.setenv("DB_URL", "sqlite+pysqlite:///:memory:")
    for s in get_db():
        res = exec_sql(s, "SELECT 2 AS v")
        row = res.fetchone()
        assert row[0] == 2


def test_exec_sql_one_arg_returns_rows(monkeypatch):
    monkeypatch.setenv("DB_URL", "sqlite+pysqlite:///:memory:")
    rows = exec_sql("SELECT 3 AS v")
    assert rows[0][0] == 3
