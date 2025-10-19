"""add sitegen runs/events tables
Revision ID: 20251019_add_sitegen
Revises: 20251015_add_site_section_table
Create Date: 2025-10-19

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251019_add_sitegen"
down_revision = "20251015_add_site_section_table"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sitegen_runs",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("project_id", sa.String(length=128), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False, index=True),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("result", sa.JSON, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "sitegen_events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=32), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )


def downgrade():
    op.drop_table("sitegen_events")
    op.drop_table("sitegen_runs")
