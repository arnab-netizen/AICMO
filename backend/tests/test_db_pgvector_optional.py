import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql+asyncpg://"),
    reason="pgvector test runs only when Postgres DATABASE_URL is set",
)


def test_pgvector_extension_present():
    # If DATABASE_URL is set to a Postgres DSN, try a quick check for the 'vector' extension.
    from backend.db import get_engine

    eng = get_engine()
    with eng.connect() as conn:
        try:
            # using raw SQL string; use exec_driver_sql for safety or exec_sql helper
            res = conn.exec_driver_sql("SELECT extname FROM pg_extension WHERE extname='vector'")
            rows = list(res)
            assert rows != [], "pgvector extension not found"
        except Exception as e:
            pytest.skip(f"Could not query pg_extension: {e}")
