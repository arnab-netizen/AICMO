from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import os
import sys

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Make sure the project root is on the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


# --- DEFINITIVE FIX ---
# Import the Base class, which is the foundation for your models.
from backend.db.base import Base  # noqa

# Import all modules that contain your SQLAlchemy models.
# By importing these files, you tell Alembic that these tables exist.
# Without this, Alembic will think the tables should be dropped.
import backend.models  # noqa
import backend.modules.sitegen.db_models  # noqa
import app.models  # noqa

# Phase 4 Lane B: AICMO business module models
import aicmo.cam.db_models  # noqa (30+ CAM tables - must import to prevent drops)
import aicmo.onboarding.internal.models  # noqa
import aicmo.strategy.internal.models  # noqa
import aicmo.production.internal.models  # noqa
import aicmo.delivery.internal.models  # noqa

# Fast Revenue Marketing Engine (venture module)
import aicmo.venture.models  # noqa
import aicmo.venture.distribution_models  # noqa
import aicmo.venture.audit  # noqa

# Campaign Orchestrator (Phase 2)
import aicmo.cam.orchestrator.models  # noqa

# Autonomy Orchestration Layer (AOL) - daemon, queue, lease
import aicmo.orchestration.models  # noqa

# TODO: Add qc, delivery models as they're implemented

# --- END DEFINITIVE FIX ---


# Set the target_metadata for Alembic's autogenerate feature.
# Because we imported all models above, Base.metadata will now contain
# a complete list of all your tables.
target_metadata = Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = os.getenv("DATABASE_URL_SYNC") or config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    url = os.getenv("DATABASE_URL_SYNC") or config.get_main_option("sqlalchemy.url")
    connectable = engine_from_config(
        {"sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
