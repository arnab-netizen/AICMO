import sys
import types
from contextlib import contextmanager
from importlib import import_module, reload


def _inject_fake_alembic():
    """Create a minimal `alembic` module with `context.config.get_main_option` so
    importing `backend.alembic.env` during tests does not fail at module import.
    """
    mod = types.ModuleType("alembic")

    # create a minimal config object with needed methods
    class _Config:
        def __init__(self):
            self._opts = {}
            self.config_file_name = None
            self.config_ini_section = "alembic"

        def get_main_option(self, key):
            return self._opts.get(key)

        def set_main_option(self, key, value):
            self._opts[key] = value

        def get_section(self, section):
            # minimal empty section mapping used by engine_from_config
            return {}

    # build a fake context with no-op migration helpers so importing env.py
    # won't attempt any real DB work during tests
    cfg = _Config()

    @contextmanager
    def _begin_transaction():
        yield

    class _Ctx:
        def __init__(self, config):
            self.config = config

        def configure(self, *a, **kw):
            return None

        def begin_transaction(self):
            return _begin_transaction()

        def run_migrations(self):
            return None

        def is_offline_mode(self):
            # default to offline so we don't attempt to create engines
            return True

    ctx = _Ctx(cfg)
    mod.context = ctx
    # place into sys.modules so `from alembic import context` works
    sys.modules["alembic"] = mod
    sys.modules["alembic.context"] = ctx


def test_sync_url_swap_asyncpg_to_psycopg2(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h:5432/db")
    _inject_fake_alembic()
    # import after injection so env.py sees our fake alembic.context
    alembic_env = import_module("backend.alembic.env")
    # reload to ensure any module-level reads are fresh
    reload(alembic_env)
    url = alembic_env._sync_url()
    assert url is not None
    assert url.startswith("postgresql+psycopg2://")
    assert "asyncpg" not in url


def test_sync_url_keeps_sync_driver(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://u:p@h:5432/db")
    _inject_fake_alembic()
    alembic_env = import_module("backend.alembic.env")
    reload(alembic_env)
    url = alembic_env._sync_url()
    assert url == "postgresql+psycopg2://u:p@h:5432/db"
