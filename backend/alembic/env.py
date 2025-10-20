import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config
try:
    # fileConfig will attempt to read logger_* sections; if alembic.ini is minimal
    # we tolerate missing logging config to keep migrations robust in CI/dev.
    fileConfig(config.config_file_name)
except Exception:
    pass

# Read DB URL from DB_URL or DATABASE_URL env vars (fallback to sqlite memory)
# We do not set the sqlalchemy.url here immediately — instead we prefer to
# derive a sync URL (if the app uses an async driver) and set the final value
# after _sync_url() is able to inspect environment/config.
db_url = os.getenv("DB_URL") or os.getenv("DATABASE_URL") or "sqlite+pysqlite:///:memory:"


def _sync_url() -> str | None:
    """Return a sync SQLAlchemy URL for Alembic when the app uses an async driver.

    If the configured DSN uses an async driver like +asyncpg, replace it with a
    sync driver (psycopg2). This keeps the application running with asyncpg while
    allowing Alembic to run migrations synchronously.
    """
    url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    if not url:
        return None
    # Swap asyncpg to a sync driver suitable for Alembic migrations. We choose
    # psycopg2-binary here; if you prefer psycopg v3, replace with '+psycopg'.
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg2")
    return url


# Note: we intentionally defer setting config.sqlalchemy.url until runtime.
# Online and offline migration paths have different requirements: online
# migrations need a live Postgres URL (we guard that), while offline
# (--sql) rendering should be allowed without a live DB.


# If you have target metadata (models) you can set it here. We don't rely on it for raw SQL migrations.
target_metadata = None


def run_migrations_offline():
    # Allow offline SQL rendering without requiring a live Postgres instance.
    # Use the sync-swapped URL if present, otherwise fall back to the config
    # value; if neither exists provide a harmless dummy for rendering.
    url = _sync_url() or config.get_main_option("sqlalchemy.url") or ""
    context.configure(
        url=url or "postgresql+psycopg2://",
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    # In online mode we require a Postgres URL (swap async to psycopg2 if needed)
    chosen_url = _sync_url() or db_url
    if not chosen_url or not chosen_url.startswith("postgresql"):
        raise RuntimeError("Alembic requires a Postgres DATABASE_URL for online migrations.")
    config.set_main_option("sqlalchemy.url", chosen_url)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
