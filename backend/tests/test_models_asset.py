import os
import sqlalchemy as sa
from sqlalchemy.orm import Session
from backend.models import Base, Asset  # assumes Base is exported


def test_asset_orm_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_URL", f"sqlite+pysqlite:///{tmp_path / 't.db'}")
    eng = sa.create_engine(os.environ["DB_URL"])
    # Create only the Asset table to avoid collisions with other models' indexes
    from backend.models import Asset as _Asset

    Base.metadata.create_all(eng, tables=[_Asset.__table__])

    with Session(eng) as s:
        a = Asset(
            name="demo",
            taste_score=0.8,
            emotion_score=0.5,
            tone="minimal",
            brand_alignment=0.9,
        )
        s.add(a)
        s.commit()
        s.refresh(a)
        got = s.get(Asset, a.id)
        assert got.name == "demo"
        assert got.tone == "minimal"
