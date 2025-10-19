"""ensure pgvector extension exists

Revision ID: 20251019_pgvector_guard
Revises: 20251019_taste
Create Date: 2025-10-19 00:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251019_pgvector_guard"
down_revision = "20251019_taste"
branch_labels = None
depends_on = None


def upgrade():
    # Idempotent: succeeds if already present
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def downgrade():
    # Keep extension; downgrading would be destructive across other objects
    pass
