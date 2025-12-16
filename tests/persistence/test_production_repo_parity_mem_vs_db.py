"""
Test Production repository parity (mem vs db).

Validates that InMemoryProductionRepo and DatabaseProductionRepo
produce identical observable behavior for same operations.

Parity tests ensure dual-mode (inmemory/db) works transparently.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aicmo.core.db import Base
from aicmo.production.internal.repositories_mem import InMemoryProductionRepo
from aicmo.production.internal.repositories_db import DatabaseProductionRepo
from aicmo.production.api.dtos import ContentDraftDTO, DraftBundleDTO, AssetDTO


@pytest.fixture
def mem_repo():
    """In-memory repository."""
    return InMemoryProductionRepo()


@pytest.fixture
def db_repo(monkeypatch):
    """Database repository with in-memory SQLite."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    repo = DatabaseProductionRepo()
    
    # Mock get_session
    from contextlib import contextmanager
    @contextmanager
    def mock_get_session():
        yield session
    
    monkeypatch.setattr(repo, "_get_session", mock_get_session)
    return repo


@pytest.fixture
def sample_draft():
    """Sample content draft."""
    return ContentDraftDTO(
        draft_id="draft_parity_123",
        strategy_id="strategy_parity_456",
        content_type="blog_post",
        body="# Parity Test Blog Post",
        metadata={"word_count": 1500},
        created_at=datetime(2025, 12, 13, 10, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_bundle(sample_draft):
    """Sample draft bundle with assets."""
    assets = [
        AssetDTO(
            asset_id="asset_parity_img_1",
            asset_type="image",
            url="https://example.com/image.jpg",
            metadata={"width": 1200},
        ),
    ]
    return DraftBundleDTO(
        bundle_id="bundle_parity_789",
        draft_id=sample_draft.draft_id,
        assets=assets,
        assembled_at=datetime(2025, 12, 13, 11, 0, 0, tzinfo=timezone.utc),
    )


def test_save_and_get_draft_parity(mem_repo, db_repo, sample_draft):
    """Both repos: save draft → get draft → identical results."""
    mem_repo.save_draft(sample_draft)
    db_repo.save_draft(sample_draft)
    
    mem_result = mem_repo.get_draft(sample_draft.draft_id)
    db_result = db_repo.get_draft(sample_draft.draft_id)
    
    assert mem_result.draft_id == db_result.draft_id
    assert mem_result.strategy_id == db_result.strategy_id
    assert mem_result.content_type == db_result.content_type
    assert mem_result.body == db_result.body
    assert mem_result.metadata == db_result.metadata


def test_idempotent_save_draft_parity(mem_repo, db_repo, sample_draft):
    """Both repos: save twice → last write wins."""
    # First save
    mem_repo.save_draft(sample_draft)
    db_repo.save_draft(sample_draft)
    
    # Second save with different content
    updated_draft = ContentDraftDTO(
        draft_id=sample_draft.draft_id,
        strategy_id=sample_draft.strategy_id,
        content_type="whitepaper",
        body="# Updated",
        metadata={"word_count": 2000},
        created_at=sample_draft.created_at,
    )
    mem_repo.save_draft(updated_draft)
    db_repo.save_draft(updated_draft)
    
    mem_result = mem_repo.get_draft(sample_draft.draft_id)
    db_result = db_repo.get_draft(sample_draft.draft_id)
    
    assert mem_result.content_type == "whitepaper"
    assert db_result.content_type == "whitepaper"


def test_get_nonexistent_draft_parity(mem_repo, db_repo):
    """Both repos: get nonexistent draft → None."""
    mem_result = mem_repo.get_draft("nonexistent_parity")
    db_result = db_repo.get_draft("nonexistent_parity")
    
    assert mem_result is None
    assert db_result is None


def test_save_and_get_bundle_parity(mem_repo, db_repo, sample_bundle):
    """Both repos: save bundle → get bundle → identical results."""
    mem_repo.save_bundle(sample_bundle)
    db_repo.save_bundle(sample_bundle)
    
    mem_result = mem_repo.get_bundle(sample_bundle.bundle_id)
    db_result = db_repo.get_bundle(sample_bundle.bundle_id)
    
    assert mem_result.bundle_id == db_result.bundle_id
    assert mem_result.draft_id == db_result.draft_id
    assert len(mem_result.assets) == len(db_result.assets)
    assert mem_result.assets[0].asset_id == db_result.assets[0].asset_id


def test_get_nonexistent_bundle_parity(mem_repo, db_repo):
    """Both repos: get nonexistent bundle → None."""
    mem_result = mem_repo.get_bundle("nonexistent_bundle_parity")
    db_result = db_repo.get_bundle("nonexistent_bundle_parity")
    
    assert mem_result is None
    assert db_result is None
