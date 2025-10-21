"""create site_spec view

Revision ID: 20251022_create_site_spec_view
Revises: 20251022_page_unique_index
Create Date: 2025-10-21 02:00:00.000000
"""

from alembic import op

revision = "20251022_create_site_spec_view"
down_revision = "20251022_page_unique_index"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE OR REPLACE VIEW site_spec AS
        SELECT
          s.slug,
          COALESCE((SELECT json_agg(json_build_object('id', p.id, 'path', p.path, 'title', p.title, 'seo', p.seo)) FROM page p WHERE p.site_id = s.id), '[]'::json) AS pages,
          COALESCE((SELECT json_agg(json_build_object('id', ss.id, 'type', ss."type", 'props', ss.props, 'order', ss."order")) FROM site_section ss WHERE ss.site_id = s.id), '[]'::json) AS sections
        FROM site s;
        """
    )


def downgrade():
    op.execute("DROP VIEW IF EXISTS site_spec CASCADE;")
