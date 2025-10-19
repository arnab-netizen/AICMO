-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Add taste-related columns (idempotent)
ALTER TABLE assets
    ADD COLUMN IF NOT EXISTS taste_score NUMERIC(3,1),
    ADD COLUMN IF NOT EXISTS emotion_score NUMERIC(3,2),
    ADD COLUMN IF NOT EXISTS tone TEXT,
    ADD COLUMN IF NOT EXISTS brand_alignment NUMERIC(3,2),
    ADD COLUMN IF NOT EXISTS embedding VECTOR(1536);

-- Useful indexes
CREATE INDEX IF NOT EXISTS idx_assets_taste_score ON assets (taste_score);
CREATE INDEX IF NOT EXISTS idx_assets_brand_alignment ON assets (brand_alignment);

-- ANN index for cosine similarity (tune lists for your data size)
CREATE INDEX IF NOT EXISTS idx_assets_embedding_ivf
ON assets USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
