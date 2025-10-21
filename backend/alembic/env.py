import os
from pathlib import Path
import sys

# --- sys.path bootstrap so `import backend` works when Alembic runs from backend/alembic
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
# ---

from logging.config import fileConfig  # noqa: E402
from sqlalchemy import engine_from_config, pool  # noqa: E402
from alembic import context  # noqa: E402

# Import metadata and model modules at top so linters are happy and autogenerate
from backend.db.base import Base  # your metadata  # noqa: E402
import backend  # noqa: F401,E402
import backend.models  # noqa: F401,E402

# Some unit tests inject a fake `alembic.context` (SimpleNamespace) which may
# not provide a `config` object. Make env.py tolerant: if `context.config` is
# missing, create a minimal dummy config that implements the few methods
# env.py uses (get_main_option, set_main_option, get_section, config_file_name).
if getattr(context, "config", None) is not None:
    config = context.config
else:

    class _DummyConfig:
        config_file_name = None
        config_ini_section = "alembic"

        def get_main_option(self, key, default=None):
            # Prefer explicit SQLALCHEMY_URL override from env in test scenarios
            return os.getenv("SQLALCHEMY_URL") or default

        def set_main_option(self, key, value):
            # No-op for dummy config used during tests
            return None

        def get_section(self, section):
            return {}

    config = _DummyConfig()

try:
    # fileConfig will attempt to read logger_* sections; if alembic.ini is minimal
    # we tolerate missing logging config to keep migrations robust in CI/dev.
    fileConfig(config.config_file_name)
except Exception:
    pass


# Allow CI to override the alembic URL explicitly (used by the drift probe)
# Example: SQLALCHEMY_URL=sqlite:////github/workspace/.alembic_tmp/drift.sqlite
_override_url = os.getenv("SQLALCHEMY_URL")
if _override_url:
    config.set_main_option("sqlalchemy.url", _override_url)


def _sync_url() -> str | None:
    """Return a sync SQLAlchemy URL for Alembic when the app uses an async driver.

    If the configured DSN uses an async driver like +asyncpg, replace it with a
    sync driver (psycopg2). This keeps the application running with asyncpg while
    allowing Alembic to run migrations synchronously.
    """
    url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    if not url:
        return None
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg2")
    return url


# Use model metadata so autogenerate can compare types/defaults
target_metadata = Base.metadata


def run_migrations_offline():
    # Allow offline SQL rendering without requiring a live Postgres instance.
    # Use the sync-swapped URL if present, otherwise fall back to the config
    # value; if neither exists provide a harmless dummy for rendering.
    url = _sync_url() or config.get_main_option("sqlalchemy.url") or ""
    context.configure(
        url=url or "postgresql+psycopg2://",
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )
    # Some unit tests provide a fake `begin_transaction` that returns a
    # SimpleNamespace. Be defensive: if the returned object doesn't support
    # the context manager protocol, fall back to calling run_migrations()
    # directly.
    try:
        txn = context.begin_transaction()
        if hasattr(txn, "__enter__") and callable(getattr(txn, "__enter__")):
            with txn:
                context.run_migrations()
        else:
            context.run_migrations()
    except TypeError:
        context.run_migrations()


def run_migrations_online():
    # NEW: force offline if env asks for it
    if os.getenv("ALEMBIC_OFFLINE") == "1":
        return run_migrations_offline()

    # Respect -x offline=1 to force offline path (keeps compatibility)
    if context.get_x_argument(as_dictionary=True).get("offline") == "1":
        return run_migrations_offline()

    # In online mode we normally require a Postgres URL (swap async to psycopg2 if needed)
    # but for CI drift probing we also allow a sqlite temporary DB when explicitly
    # provided via SQLALCHEMY_URL or DATABASE_URL.
    chosen_url = _sync_url() or os.getenv("DB_URL") or os.getenv("DATABASE_URL")
    if not chosen_url:
        raise RuntimeError("Alembic requires a DATABASE_URL for online migrations.")

    # Allow sqlite for CI drift probe (e.g. sqlite:///.../.alembic_tmp/drift.sqlite)
    if not (chosen_url.startswith("postgresql") or chosen_url.startswith("sqlite")):
        raise RuntimeError("Alembic requires a Postgres DATABASE_URL for online migrations.")

    config.set_main_option("sqlalchemy.url", chosen_url)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
        )
        # Same defensive handling for begin_transaction as offline mode.
        try:
            txn = context.begin_transaction()
            if hasattr(txn, "__enter__") and callable(getattr(txn, "__enter__")):
                with txn:
                    context.run_migrations()
            else:
                context.run_migrations()
        except TypeError:
            context.run_migrations()


if context.is_offline_mode() or os.getenv("ALEMBIC_OFFLINE") == "1":
    run_migrations_offline()
else:
    run_migrations_online()
