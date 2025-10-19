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
db_url = os.getenv("DB_URL") or os.getenv("DATABASE_URL") or "sqlite+pysqlite:///:memory:"
config.set_main_option("sqlalchemy.url", db_url)

# If you have target metadata (models) you can set it here. We don't rely on it for raw SQL migrations.
target_metadata = None


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
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
