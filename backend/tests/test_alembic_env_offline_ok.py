import importlib
import types
import builtins
import sys


def test_offline_mode_does_not_require_postgres(monkeypatch):
    # Fake minimal alembic context with offline mode
    fake_ctx = types.SimpleNamespace()

    def is_offline_mode():
        return True

    def configure(**kwargs):
        fake_ctx.kwargs = kwargs

    def begin_transaction():
        return types.SimpleNamespace(__enter__=lambda s: s, __exit__=lambda s, *a: False)

    def run_migrations():
        return None

    fake_alembic = types.SimpleNamespace(
        context=types.SimpleNamespace(
            is_offline_mode=is_offline_mode,
            configure=configure,
            begin_transaction=begin_transaction,
            run_migrations=run_migrations,
        )
    )

    # Inject fake alembic before import
    monkeypatch.setitem(builtins.__dict__, "__alembic_fake__", True)
    sys.modules["alembic"] = fake_alembic
    sys.modules["alembic.context"] = fake_alembic.context

    # Ensure no DATABASE_URL set; offline should still import & configure
    monkeypatch.delenv("DATABASE_URL", raising=False)

    # Import env.py; it should configure offline without raising
    env = importlib.import_module("backend.alembic.env")
    assert hasattr(env, "_sync_url")
