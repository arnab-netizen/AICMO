"""add site.title column

Revision ID: 20251021_add_site_title
Revises: d629c4a0a1b7
Create Date: 2025-10-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20251021_add_site_title"
down_revision = "d629c4a0a1b7"
branch_labels = None
depends_on = None


def upgrade():
    # Add a nullable title column; use type compatible with Postgres and SQLite
    try:
        op.add_column("site", sa.Column("title", sa.Text(), nullable=True))
    except Exception:
        # Some backends or DDL contexts may raise if column exists; ignore
        pass


def downgrade():
    try:
        op.drop_column("site", "title")
    except Exception:
        pass
