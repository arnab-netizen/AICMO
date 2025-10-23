import os
import random
import argparse
from typing import Optional
from sqlalchemy import text, create_engine
from backend.db import get_engine


def main(url: Optional[str] = None):
    """Seed demo assets.

    If `url` is provided, build a sync Engine from that URL and use it.
    Otherwise fall back to the project's runtime helper `get_engine()`.
    """
    random.seed(42)
    if url:
        # Create a sync engine directly from the provided URL. Keep connect
        # args compatible with the session helpers (sqlite uses check_same_thread).
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args, future=True)
    else:
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


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Seed demo taste assets")
    p.add_argument("--url", help="Optional DB URL to use for seeding (overrides env)")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    # If no explicit url provided, ensure some env var exists for convenience
    if not args.url and "DB_URL" not in os.environ and "DATABASE_URL" not in os.environ:
        raise SystemExit("Set DB_URL or DATABASE_URL or provide --url")
    main(url=args.url)
