# Ensure the cov_unit_targets fanout module is imported during pytest collection
import backend.cov_unit_targets  # noqa: F401

import pytest
from starlette.testclient import TestClient
import os
import random
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import get_engine

# Use the fully-wired application which includes all routers used in tests
from backend.app import app

# CAM test database setup
from aicmo.cam.db_models import (
    Base as CAMBase,
    CampaignDB,
    LeadDB,
    DiscoveryJobDB,
    DiscoveredProfileDB,
    OutreachAttemptDB,
)

# Create dedicated test engine for CAM tests
TEST_DB_URL = "sqlite:///:memory:"
cam_test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},  # Critical for TestClient threading
    poolclass=StaticPool,  # Critical for in-memory SQLite to share connection
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cam_test_engine)


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


@pytest.fixture(scope="session", autouse=True)
def ensure_runs_and_artifacts_tables():
    """Create minimal `runs` and `artifacts` tables for tests running against
    the default in-memory SQLite DB so endpoints that persist runs/artifacts
    don't fail with missing tables. This is intentionally minimal and
    idempotent across runs.
    """
    engine = get_engine()
    from sqlalchemy import MetaData, Table, Column, String, Integer, Text

    metadata = MetaData()
    Table(
        "runs",
        metadata,
        Column("run_id", String, primary_key=True),
        Column("module", String),
        Column("status", String),
        Column("version", String),
        Column("tokens_used", Integer),
        Column("seconds_used", Integer),
        Column("cost_estimate", String),
    )
    Table(
        "artifacts",
        metadata,
        Column("artifact_id", String, primary_key=True),
        Column("run_id", String),
        Column("type", String),
        Column("path", Text),
        Column("meta_json", Text),
        Column("sha256", String),
        Column("size_bytes", Integer),
        Column("content_type", String),
    )

    metadata.create_all(engine)


@pytest.fixture(scope="session", autouse=True)
def setup_cam_test_db():
    """
    Create CAM database tables once per test session.
    
    This ensures all CAM tables (campaigns, leads, discovery jobs, profiles)
    exist in the test database before any CAM API tests run.
    """
    # Create only CAM-specific tables (not all Base tables which include SiteGen)
    cam_tables = [
        CampaignDB.__table__,
        LeadDB.__table__,
        OutreachAttemptDB.__table__,
        DiscoveryJobDB.__table__,
        DiscoveredProfileDB.__table__,
    ]
    CAMBase.metadata.create_all(bind=cam_test_engine, tables=cam_tables)
    yield
    # Cleanup after all tests
    CAMBase.metadata.drop_all(bind=cam_test_engine, tables=cam_tables)


@pytest.fixture(scope="function", autouse=True)
def clear_cam_data():
    """
    Clear all CAM data before each test to ensure test isolation.
    
    Uses raw DELETE statements to avoid session conflicts.
    Tables are created by setup_cam_test_db (session-scoped, autouse) which runs first.
    """
    # Use raw SQL DELETE statements for clean isolation
    with cam_test_engine.begin() as conn:
        # Try to delete, but catch errors if tables don't exist yet
        try:
            conn.execute(text("DELETE FROM outreach_attempts"))
            conn.execute(text("DELETE FROM discovered_profiles"))
            conn.execute(text("DELETE FROM discovery_jobs"))
            conn.execute(text("DELETE FROM leads"))
            conn.execute(text("DELETE FROM campaigns"))
        except Exception:
            # Tables don't exist yet - this is OK for first test
            pass
    yield
    # No cleanup needed after test - next test will clear before it runs


@pytest.fixture
def test_db():
    """
    Provide a CAM test database session for individual tests.
    
    Each test gets a fresh session that's automatically closed after use.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
