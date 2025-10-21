# Ensure the cov_unit_targets fanout module is imported during pytest collection
import backend.cov_unit_targets  # noqa: F401

import pytest
from starlette.testclient import TestClient
import os
import random
from sqlalchemy import text

from backend.db import get_engine

# Use the fully-wired application which includes all routers used in tests
from backend.app import app


@pytest.fixture(scope="module")
def client():
    # Use the fully-wired `app` from backend.app which already includes
    # sitegen, sitegen_draft, sites_compat, deployments, workflows, etc.
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session", autouse=True)
def seed_taste_demo_if_postgres():
    """Ensure a minimal 'assets' table with at least one embedded row exists when
    running tests against a Postgres/Neon DB (DB_URL/DATABASE_URL set).

    This keeps taste integration tests deterministic: if a remote Neon DB is
    provided we idempotently create the table, add taste columns if missing,
    and insert a single demo row (id=1) with a random embedding.
    """
    db_url = os.environ.get("DB_URL") or os.environ.get("DATABASE_URL")
    if not db_url or not db_url.startswith("postgresql"):
        return

    engine = get_engine()
    emb = [random.random() for _ in range(1536)]
    with engine.begin() as cx:
        # create minimal table if missing
        cx.execute(
            text(
                """
        CREATE TABLE IF NOT EXISTS assets(
          id BIGINT PRIMARY KEY,
          name TEXT NOT NULL
        );
        """
            )
        )
        # add taste/vector columns if missing
        cx.execute(text("ALTER TABLE assets ADD COLUMN IF NOT EXISTS taste_score NUMERIC;"))
        cx.execute(text("ALTER TABLE assets ADD COLUMN IF NOT EXISTS emotion_score NUMERIC;"))
        cx.execute(text("ALTER TABLE assets ADD COLUMN IF NOT EXISTS tone TEXT;"))
        cx.execute(text("ALTER TABLE assets ADD COLUMN IF NOT EXISTS brand_alignment NUMERIC;"))
        cx.execute(text("ALTER TABLE assets ADD COLUMN IF NOT EXISTS embedding VECTOR(1536);"))

        # Insert id=1 demo row if it doesn't exist
        cx.execute(
            text(
                """
            INSERT INTO assets (id, name, taste_score, emotion_score, tone, brand_alignment, embedding)
            VALUES (:id, :n, :t, :e, :tone, :b, :emb)
            ON CONFLICT (id) DO NOTHING;
            """
            ),
            {
                "id": 1,
                "n": "seeded_asset_1",
                "t": 0.75,
                "e": 0.5,
                "tone": "minimal",
                "b": 0.8,
                "emb": emb,
            },
        )
