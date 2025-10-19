from __future__ import annotations

from typing import List, Optional, Any
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_session

from backend.modules.taste.service import TasteRecord, record_taste, similar_assets
from backend.db import get_db
from backend.models import Asset
from time import perf_counter

try:
    from backend.core.utils.determinism import estimate_cost
except Exception:

    def estimate_cost(*args, **kwargs):
        return 0.0


from prometheus_client import Counter, Histogram

taste_requests = Counter("taste_compare_requests_total", "Taste compare requests")
taste_success = Counter("taste_compare_success_total", "Taste compare successes")
taste_latency = Histogram("taste_compare_seconds", "Latency of taste compare")


router = APIRouter(prefix="/taste", tags=["taste"])


def _guard(x_api_key: str | None = Header(None)) -> None:
    """Simple header guard. If TASTE_API_KEY is set, require it; otherwise allow requests in dev."""
    import os

    expected = os.environ.get("TASTE_API_KEY", "")
    if expected:
        if not x_api_key or x_api_key != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="missing/invalid API key",
            )


class RecordTasteIn(BaseModel):
    asset_id: int = Field(..., ge=1)
    taste_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    emotion_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    tone: Optional[str] = None
    brand_alignment: Optional[float] = Field(None, ge=0.0, le=1.0)
    embedding: Optional[List[float]] = Field(None, min_length=1)  # expect 1536 if provided


class AssetOut(BaseModel):
    id: int
    taste_score: Optional[float] = None
    emotion_score: Optional[float] = None
    tone: Optional[str] = None
    brand_alignment: Optional[float] = None

    @classmethod
    def from_orm_asset(cls, a: Asset) -> "AssetOut":
        return cls(
            id=a.id,
            emotion_score=(float(a.emotion_score) if a.emotion_score is not None else None),
            tone=a.tone,
            brand_alignment=(float(a.brand_alignment) if a.brand_alignment is not None else None),
        )


class RecordTasteOut(BaseModel):
    asset: AssetOut


@router.post("/record", response_model=RecordTasteOut, status_code=status.HTTP_200_OK)
def api_record_taste(payload: RecordTasteIn, db: Session = Depends(get_db)) -> RecordTasteOut:
    try:

        def _to_decimal(x: Any) -> Decimal | None:
            if x is None:
                return None
            if isinstance(x, Decimal):
                return x
            return Decimal(str(x))

        asset = record_taste(
            db,
            TasteRecord(
                asset_id=payload.asset_id,
                taste_score=(
                    None
                    if payload.taste_score is None
                    else _to_decimal(round(payload.taste_score, 1))
                ),
                emotion_score=(
                    None
                    if payload.emotion_score is None
                    else _to_decimal(round(payload.emotion_score, 2))
                ),
                tone=payload.tone,
                brand_alignment=(
                    None
                    if payload.brand_alignment is None
                    else _to_decimal(round(payload.brand_alignment, 2))
                ),
                embedding=payload.embedding,
            ),
        )
        return RecordTasteOut(asset=AssetOut.from_orm_asset(asset))

    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/typed-example", status_code=status.HTTP_200_OK)
async def typed_example(db: AsyncSession = Depends(get_session)) -> dict:
    """Small example endpoint showing a typed AsyncSession FastAPI dependency.

    This endpoint intentionally does not use the DB; it's only a typing boundary example
    to reduce mypy propagation of 'Any' at the FastAPI edge.
    """
    return {"status": "ok", "session_type": type(db).__name__}


EMBED_DIM = 1536


class CompareIn(BaseModel):
    embedding: List[float]
    top_k: int = Field(10, ge=1, le=50)
    min_taste: Optional[float] = Field(None, ge=0.0, le=10.0)

    @field_validator("embedding")
    @classmethod
    def check_dim(cls, v: List[float]) -> List[float]:
        if len(v) != EMBED_DIM:
            raise ValueError(f"embedding must be exactly {EMBED_DIM} floats")
        return v


class CompareResult(BaseModel):
    id: int
    name: Optional[str] = None
    taste_score: Optional[float] = None
    brand_alignment: Optional[float] = None
    similarity: float


class CompareResponse(BaseModel):
    results: List[CompareResult]


@router.get("/version")
def version():
    return {"name": "taste", "module": "taste", "version": "1.0.0"}


@router.post(
    "/compare",
    response_model=CompareResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(_guard)],
)
def api_compare(payload: CompareIn, db: Session = Depends(get_db)) -> CompareResponse:
    taste_requests.inc()
    t0 = perf_counter()
    rows = similar_assets(db, payload.embedding, payload.top_k, payload.min_taste)
    seconds = perf_counter() - t0
    taste_latency.observe(seconds)
    results = []
    for item, sim in rows:
        results.append(
            CompareResult(
                id=item["id"],
                name=item.get("name"),
                taste_score=item.get("taste_score"),
                brand_alignment=item.get("brand_alignment"),
                similarity=round(item.get("similarity", sim), 6),
            )
        )
    taste_success.inc()
    # estimate_cost(tokens_used) signature is tokens_used, unit_cost_per_1k_tokens
    try:
        _ = estimate_cost(0)
    except Exception:
        pass
    return CompareResponse(results=results)
