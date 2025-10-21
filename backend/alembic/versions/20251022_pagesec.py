"""create page and site_section tables (short id)

Revision ID: 20251022_pagesec
Revises: 20251022_make_site_name_nullable
Create Date: 2025-10-21 01:00:00.000000
"""

from alembic import op

revision = "20251022_pagesec"
down_revision = "20251022_make_site_name_nullable"
branch_labels = None
depends_on = None


def upgrade():
    # Use raw SQL with IF NOT EXISTS to be idempotent across runs
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS page (
          id BIGSERIAL PRIMARY KEY,
          site_id BIGINT NOT NULL REFERENCES site(id) ON DELETE CASCADE,
          path TEXT NOT NULL,
          title TEXT,
          seo JSONB,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS site_section (
          id BIGSERIAL PRIMARY KEY,
          site_id BIGINT NOT NULL REFERENCES site(id) ON DELETE CASCADE,
          "type" TEXT NOT NULL,
          props JSONB,
          "order" INTEGER DEFAULT 0
        );
        """
    )


def downgrade():
    # Best-effort drop; may be unsafe in production but fine for test repo
    op.execute("DROP TABLE IF EXISTS site_section CASCADE;")
    op.execute("DROP TABLE IF EXISTS page CASCADE;")
