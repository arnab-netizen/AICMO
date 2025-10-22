"""create sitegen runs and events

Revision ID: 20251022_create_sitegen_tables
Revises: 20251022_create_site_spec_view
Create Date: 2025-10-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251022_create_sitegen_tables"
down_revision = "20251022_create_site_spec_view"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sitegen_runs",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("project_id", sa.String(length=128), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False, index=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )
    # create index if not exists (Postgres supports IF NOT EXISTS)
    op.execute("CREATE INDEX IF NOT EXISTS ix_sitegen_runs_state ON sitegen_runs (state);")

    op.create_table(
        "sitegen_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=32), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )


def downgrade() -> None:
    op.drop_table("sitegen_events")
    op.drop_index("ix_sitegen_runs_state", table_name="sitegen_runs")
    op.drop_table("sitegen_runs")
