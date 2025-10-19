import os
import random
from sqlalchemy import text
from backend.db import get_engine


def main():
    random.seed(42)
    engine = get_engine()
    with engine.begin() as cx:
        # ensure minimal assets table exists (id + name)
        cx.execute(
            text(
                """
        CREATE TABLE IF NOT EXISTS assets(
          id SERIAL PRIMARY KEY,
          name TEXT NOT NULL
        );
        """
            )
        )
        # add taste columns if missing (safe idempotent guards)
        cx.execute(text("ALTER TABLE assets ADD COLUMN IF NOT EXISTS taste_score NUMERIC;"))
        cx.execute(text("ALTER TABLE assets ADD COLUMN IF NOT EXISTS emotion_score NUMERIC;"))
        cx.execute(text("ALTER TABLE assets ADD COLUMN IF NOT EXISTS tone TEXT;"))
        cx.execute(text("ALTER TABLE assets ADD COLUMN IF NOT EXISTS brand_alignment NUMERIC;"))
        cx.execute(text("ALTER TABLE assets ADD COLUMN IF NOT EXISTS embedding VECTOR(1536);"))

        # insert 5 demo rows with randomish embeddings
        for i in range(5):
            emb = [random.random() for _ in range(1536)]
            cx.execute(
                text(
                    """
                INSERT INTO assets (name, taste_score, emotion_score, tone, brand_alignment, embedding)
                VALUES (:n, :t, :e, :tone, :b, :emb)
            """
                ),
                {
                    "n": f"asset_{i + 1}",
                    "t": round(random.uniform(0.5, 0.95), 2),
                    "e": round(random.uniform(0.2, 0.9), 2),
                    "tone": random.choice(["playful", "bold", "minimal", "luxury"]),
                    "b": round(random.uniform(0.4, 0.98), 2),
                    "emb": emb,
                },
            )
    print("Seeded demo assets.")


if __name__ == "__main__":
    # project uses DB_URL in config; accept either for ad-hoc scripts
    if "DB_URL" not in os.environ and "DATABASE_URL" not in os.environ:
        raise SystemExit("Set DB_URL or DATABASE_URL")
    main()
