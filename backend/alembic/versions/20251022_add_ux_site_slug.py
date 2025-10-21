"""add unique ux_site_slug index

Revision ID: 20251022_add_ux_site_slug
Revises: 20251022_create_site_spec_view
Create Date: 2025-10-21 00:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251022_add_ux_site_slug"
down_revision = "20251022_create_sitegen_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # idempotent unique index on slug for seed-time uniqueness and ON CONFLICT
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_site_slug ON site(slug);")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ux_site_slug;")
