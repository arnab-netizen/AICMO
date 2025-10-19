from backend.db import exec_sql, get_db


def test_exec_sql_runs_select_1():
    gen = get_db()
    session = next(gen)
    try:
        result = exec_sql(session, "SELECT 1 AS one")
        row = result.fetchone()
        assert row is not None
        # Works across SQLAlchemy row types
        assert int(row[0]) == 1 or int(row.one) == 1
    finally:
        gen.close()
