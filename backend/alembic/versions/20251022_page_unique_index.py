"""add unique index on page(site_id, path)

Revision ID: 20251022_page_unique_index
Revises: 20251022_pagesec
Create Date: 2025-10-21 01:30:00.000000
"""

from alembic import op

revision = "20251022_page_unique_index"
down_revision = "20251022_pagesec"
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.create_index("page_site_path_idx", "page", ["site_id", "path"], unique=True)
    except Exception:
        # ignore if index exists or DDL not supported in this environment
        pass


def downgrade():
    try:
        op.drop_index("page_site_path_idx", table_name="page")
    except Exception:
        pass
