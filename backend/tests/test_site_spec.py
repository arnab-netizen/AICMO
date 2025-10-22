from sqlalchemy.sql import text
from sqlalchemy.exc import ProgrammingError

# --- SOLUTION ---
# Import the engine factory to ensure we use the same DB as the app
from backend.db.session import get_engine
from starlette.testclient import TestClient

# --- END SOLUTION ---


def ensure_seed():
    """
    Robustly seed the database for spec tests using the application's engine.
    This ensures data is visible to the TestClient.
    """
    engine = get_engine()
    slug = "founder-os"
    # Ensure minimal tables exist so we can insert seed rows even when migrations
    # haven't been applied in the test DB. This uses SQLAlchemy Table metadata
    # and works across SQLite and Postgres.
    from sqlalchemy import MetaData, Table, Column, Integer, String, Text

    metadata = MetaData()
    Table(
        "site",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String),
        Column("slug", String, unique=True),
        Column("title", String),
    )
    Table(
        "page",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer),
        Column("path", String),
        Column("title", String),
    )
    Table(
        "site_section",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("site_id", Integer),
        Column("type", String),
        Column("props", Text),
        Column("order", Integer),
    )

    metadata.create_all(engine)

    with engine.begin() as conn:
        # First try to find an existing site by slug. This avoids relying on
        # an ON CONFLICT clause which requires a unique constraint on slug.
        existing = conn.execute(
            text("SELECT id FROM site WHERE slug = :slug"), {"slug": slug}
        ).scalar_one_or_none()
        if existing is not None:
            site_id = existing
        else:
            try:
                res = conn.execute(
                    text(
                        """
                        INSERT INTO site (name, slug, title)
                        VALUES (:name, :slug, :title)
                        RETURNING id;
                        """
                    ),
                    {"name": "Founder OS Test", "slug": slug, "title": "Founder-OS"},
                )
                site_id = res.scalar_one()
            except ProgrammingError:
                # If the site table doesn't exist or the INSERT fails for DB schema reasons,
                # re-raise so the test fails visibly; this indicates migrations haven't been applied.
                raise

        # Insert page if missing
        existing_page = conn.execute(
            text("SELECT id FROM page WHERE site_id = :site_id AND path = :path"),
            {"site_id": site_id, "path": "/"},
        ).scalar_one_or_none()
        if existing_page is None:
            conn.execute(
                text(
                    """
                    INSERT INTO page (site_id, path, title)
                    VALUES (:site_id, :path, :title)
                    """
                ),
                {"site_id": site_id, "path": "/", "title": "Home"},
            )

        # Insert hero section if missing
        existing_section = conn.execute(
            text("SELECT id FROM site_section WHERE site_id = :site_id AND type = :type"),
            {"site_id": site_id, "type": "hero"},
        ).scalar_one_or_none()
        if existing_section is None:
            conn.execute(
                text(
                    """
                    INSERT INTO site_section (site_id, type, props, "order")
                    VALUES (:site_id, :type, :props, :order)
                    """
                ),
                {
                    "site_id": site_id,
                    "type": "hero",
                    "props": '{"headline": "Test Headline"}',
                    "order": 1,
                },
            )


def test_get_site_spec_ok(client: TestClient):
    ensure_seed()
    r = client.get("/sites/founder-os/spec")
    assert r.status_code == 200
    data = r.json()
    assert data["slug"] == "founder-os"
    assert isinstance(data["pages"], list)
    assert any(sec["type"] == "hero" for sec in data["sections"])
