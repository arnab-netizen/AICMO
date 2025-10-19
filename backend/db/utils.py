from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from typing import overload, Iterable
from sqlalchemy.engine import Result

from .session import get_engine


def ping_db() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(sa.text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


"""Database helper utilities.

exec_sql supports two calling conventions to maintain compatibility with
legacy code and newer convenience code:

- exec_sql(session, "SQL") -> returns a SQLAlchemy Result object (supports
  .fetchone()/.fetchall()). This is the two-argument form used by older
  callsites that already have a session.

- exec_sql("SQL") -> uses the package engine and returns a list of Row
  objects (convenient for short one-off admin/test calls).

The module defaults to an in-memory SQLite DSN when DB_URL/DATABASE_URL are
not set: `sqlite+pysqlite:///:memory:` (with check_same_thread=False).
"""


@overload
def exec_sql(sql: str) -> Iterable: ...


@overload
def exec_sql(session, sql: str) -> Result: ...


def exec_sql(sql_or_session, sql: str | None = None):
    """Compatibility helper implementing the two overlapping signatures.

    See module docstring for details.
    """
    # Two-arg form: (session, sql)
    if sql is not None:
        session = sql_or_session
        stmt = sql
        return session.execute(sa.text(stmt))

    # Single-arg form: (sql,)
    stmt = sql_or_session
    with get_engine().connect() as conn:
        result = conn.execute(sa.text(stmt))
        try:
            return result.fetchall()
        except Exception:
            return []
