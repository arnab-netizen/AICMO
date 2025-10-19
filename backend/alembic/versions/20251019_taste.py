from alembic import op

# revision identifiers, used by Alembic.
revision = "20251019_taste"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE TABLE IF NOT EXISTS assets(
      id SERIAL PRIMARY KEY,
      name TEXT NOT NULL
    );
    ALTER TABLE assets ADD COLUMN IF NOT EXISTS taste_score NUMERIC;
    ALTER TABLE assets ADD COLUMN IF NOT EXISTS emotion_score NUMERIC;
    ALTER TABLE assets ADD COLUMN IF NOT EXISTS tone TEXT;
    ALTER TABLE assets ADD COLUMN IF NOT EXISTS brand_alignment NUMERIC;
    ALTER TABLE assets ADD COLUMN IF NOT EXISTS embedding VECTOR(1536);
    CREATE INDEX IF NOT EXISTS idx_assets_taste ON assets (taste_score);
    CREATE INDEX IF NOT EXISTS idx_assets_brand ON assets (brand_alignment);
    CREATE INDEX IF NOT EXISTS idx_assets_embedding_ivf
      ON assets USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
    """
    )


def downgrade():
    op.execute(
        """
    DROP INDEX IF EXISTS idx_assets_embedding_ivf;
    DROP INDEX IF EXISTS idx_assets_brand;
    DROP INDEX IF EXISTS idx_assets_taste;
    -- keep table/extension to avoid data loss
    """
    )
