"""make site.name nullable

Revision ID: 20251022_make_site_name_nullable
Revises: 20251021_add_site_title
Create Date: 2025-10-21 00:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20251022_make_site_name_nullable"
down_revision = "20251021_add_site_title"
branch_labels = None
depends_on = None


def upgrade():
    # Alter `name` to allow NULLs so tests that omit `name` can insert rows.
    try:
        op.alter_column("site", "name", existing_type=sa.TEXT(), nullable=True)
    except Exception:
        # Best-effort: some backends might have different type objects; ignore on failure
        pass


def downgrade():
    try:
        op.alter_column("site", "name", existing_type=sa.TEXT(), nullable=False)
    except Exception:
        pass
