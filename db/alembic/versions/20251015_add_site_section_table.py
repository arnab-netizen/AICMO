"""
Revision ID: 20251015_add_site_section_table
Revises: None
Create Date: 2025-10-15
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251015_add_site_section_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "site_section",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("site_id", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.String(120), nullable=False),
        sa.Column("props", sa.Text(), nullable=False),
        sa.Column("order", sa.BigInteger(), nullable=False),
    )


def downgrade():
    op.drop_table("site_section")
