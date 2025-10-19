from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Sequence, Tuple, Dict, Any

from sqlalchemy import text
from sqlalchemy.orm import Session
import math

from backend.models import Asset


@dataclass(frozen=True)
class TasteRecord:
    asset_id: int
    taste_score: Optional[Decimal] = None
    emotion_score: Optional[Decimal] = None
    tone: Optional[str] = None
    brand_alignment: Optional[Decimal] = None
    embedding: Optional[Sequence[float]] = None  # 1536-dim (adjust to your chosen dim)


def record_taste(session: Session, rec: TasteRecord) -> Asset:
    asset: Asset = session.get(Asset, rec.asset_id)  # type: ignore[assignment]
    if asset is None:
        raise ValueError(f"Asset {rec.asset_id} not found")

    if rec.taste_score is not None:
        asset.taste_score = rec.taste_score
    if rec.emotion_score is not None:
        asset.emotion_score = rec.emotion_score
    if rec.tone is not None:
        asset.tone = rec.tone
    if rec.brand_alignment is not None:
        asset.brand_alignment = rec.brand_alignment
    if rec.embedding is not None:
        # pgvector accepts a Python list[float]
        asset.embedding = list(rec.embedding)

    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def similar_assets(
    session: Session,
    query_embedding: Sequence[float],
    top_k: int = 10,
    min_taste: Optional[float] = None,
) -> List[Tuple[Dict[str, Any], float]]:
    if not query_embedding:
        raise ValueError("query_embedding is empty")

    where_fragments: List[str] = ["a.embedding IS NOT NULL"]
    params = {"emb": list(query_embedding), "k": top_k}
    if min_taste is not None:
        where_fragments.append("a.taste_score >= :min_taste")
        params["min_taste"] = min_taste

    where_sql = " AND ".join(where_fragments)

    sql = text(
        f"""
        SELECT a.id, a.name, a.taste_score, a.brand_alignment,
               1 - (a.embedding <=> (:emb)::vector) AS similarity
        FROM assets AS a
        WHERE {where_sql}
        ORDER BY a.embedding <=> (:emb)::vector
        LIMIT :k
        """
    )

    rows = session.execute(sql, params).mappings().all()

    result: List[Tuple[dict, float]] = []
    for r in rows:
        raw_sim = r.get("similarity")
        try:
            sim = float(raw_sim) if raw_sim is not None else 0.0
            if math.isnan(sim) or math.isinf(sim):
                sim = 0.0
        except Exception:
            sim = 0.0

        item = {
            "id": int(r["id"]),
            "name": r.get("name"),
            "taste_score": (float(r["taste_score"]) if r.get("taste_score") is not None else None),
            "brand_alignment": (
                float(r["brand_alignment"]) if r.get("brand_alignment") is not None else None
            ),
            "similarity": sim,
        }
        result.append((item, sim))
    return result
