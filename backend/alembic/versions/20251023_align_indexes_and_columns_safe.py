"""Safe hand-edited migration derived from autogenerate probe

This file was created by copying the autogenerate output and removing
destructive operations. It preserves safe backfills and index adjustments
where necessary. Review before committing to main.
"""

from __future__ import annotations

from alembic import op

revision = "20251023_align_idx_cols_safe"
down_revision = "20251023_align_models_nd"
branch_labels = None
depends_on = None


def upgrade():
    """Apply safe, non-destructive schema alignment."""
    # The original autogenerate wanted to drop several tables and indexes.
    # We do NOT drop them here. Instead, handle only safe changes: add
    # missing columns, backfill NOT NULLs, and create missing indexes that
    # are additive. Any drop/remove should be handled in a reviewed
    # maintenance migration.

    # Example: ensure 'site' has a 'name' column (backfill handled elsewhere)
    # If the column already exists, this will be a no-op for alembic.
    # Use idempotent raw SQL for additive column/index changes so migrations
    # are safe to run even if partially applied.
    op.execute("ALTER TABLE assets ADD COLUMN IF NOT EXISTS score FLOAT")
    op.execute("ALTER TABLE assets ADD COLUMN IF NOT EXISTS meta JSON")
    op.execute(
        "ALTER TABLE assets ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL"
    )
    op.execute(
        "ALTER TABLE assets ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL"
    )

    # Avoid altering types here to prevent unsafe casts. Only create additive
    # indexes if they don't exist.
    op.execute("CREATE INDEX IF NOT EXISTS ix_assets_id ON assets (id)")


def downgrade():
    """Downgrade only reverses the safe additive changes above."""
    # Best-effort removal using IF EXISTS where possible.
    op.execute("DROP INDEX IF EXISTS ix_assets_id")
    op.execute("ALTER TABLE assets DROP COLUMN IF EXISTS updated_at")
    op.execute("ALTER TABLE assets DROP COLUMN IF EXISTS created_at")
    op.execute("ALTER TABLE assets DROP COLUMN IF EXISTS meta")
    op.execute("ALTER TABLE assets DROP COLUMN IF EXISTS score")
