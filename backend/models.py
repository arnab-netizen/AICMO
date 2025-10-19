from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, TIMESTAMP, Column, Integer, Text, Numeric
from sqlalchemy.sql import func

Base = declarative_base()


class Site(Base):
    __tablename__ = "site"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())


# --- Asset model with taste-awareness fields ---
try:
    # pgvector import optional at runtime; keep model defined even if package missing
    from pgvector.sqlalchemy import Vector  # type: ignore
except Exception:
    Vector = None  # type: ignore


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)

    # Taste-awareness fields
    taste_score = Column(Numeric(3, 1), nullable=True)
    emotion_score = Column(Numeric(3, 2), nullable=True)
    tone = Column(Text, nullable=True)
    brand_alignment = Column(Numeric(3, 2), nullable=True)
    if Vector is not None:
        embedding = Column(Vector(1536), nullable=True)
    else:
        # fallback to JSON/text if pgvector not installed; migrations still control DB
        embedding = Column(Text, nullable=True)
