"""Align models to DB (non-destructive, phased)

- Makes site.name NOT NULL via backfill + default latch (no drops).
- Adjusts site.title type to String (from TEXT) if needed (no data loss).
- Intentionally DOES NOT drop any tables or indexes.

Review notes:
- If you truly intend to drop tables/indexes, do it in a separate, reviewed migration.
- Adjust backfill/defaults to match your product semantics.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251023_align_models_nd"
down_revision = "20251022_add_ux_site_slug"
branch_labels = None
depends_on = None


def upgrade():
    # ---- site.name: make NOT NULL safely ----
    # 1) Backfill NULLs
    op.execute("""UPDATE site SET name = 'site' WHERE name IS NULL;""")

    # 2) Apply a temporary default to catch new rows during deploy window
    op.alter_column(
        "site",
        "name",
        existing_type=sa.String(),  # adjust length if your model uses one
        server_default="site",
        existing_nullable=True,
    )

    # 3) Enforce NOT NULL
    op.alter_column(
        "site",
        "name",
        existing_type=sa.String(),
        nullable=False,
        existing_server_default="site",
    )

    # 4) Drop the default (optional—keep if you want a permanent default)
    op.alter_column(
        "site",
        "name",
        existing_type=sa.String(),
        server_default=None,
        existing_nullable=False,
    )

    # ---- site.title: normalize type (TEXT -> String) non-destructively ----
    # PG allows implicit cast from TEXT -> VARCHAR/STRING (unbounded).
    # If your model uses a specific length, set type_=sa.String(<len>).
    op.alter_column(
        "site",
        "title",
        existing_type=sa.TEXT(),
        type_=sa.String(),  # or sa.String(<len>) if your model specifies it
        existing_nullable=True,
    )

    # NOTE: We intentionally DO NOT drop any tables or indexes here.
    # If autogen suggested drops for tables like page/sitegen_* etc.,
    # that was likely due to metadata exclusions/naming changes or noise.
    # Handle real removals in a dedicated migration after manual review.


def downgrade():
    # Reverse the title type change (String -> TEXT)
    op.alter_column(
        "site",
        "title",
        existing_type=sa.String(),
        type_=sa.TEXT(),
        existing_nullable=True,
    )

    # Allow NULL again for site.name and remove default if present
    op.alter_column(
        "site",
        "name",
        existing_type=sa.String(),
        server_default=None,
        existing_nullable=True,
    )
