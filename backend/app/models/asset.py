from __future__ import annotations

from sqlalchemy import Column, Integer, Text, Numeric
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector  # requires `pgvector` package

Base = declarative_base()


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    # NOTE: other existing columns (title, body, project_id, etc.) are assumed to exist elsewhere

    # --- Taste Awareness fields ---
    taste_score = Column(Numeric(3, 1), nullable=True)  # 0.0–10.0
    emotion_score = Column(Numeric(3, 2), nullable=True)  # 0.00–1.00
    tone = Column(Text, nullable=True)
    brand_alignment = Column(Numeric(3, 2), nullable=True)  # 0.00–1.00
    embedding = Column(Vector(1536), nullable=True)  # keep dim consistent with migration
