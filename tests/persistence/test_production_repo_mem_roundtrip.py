"""
Test Production in-memory repository roundtrip behavior.

Validates:
- Save/retrieve roundtrip
- Idempotency (save same draft_id twice)
- Read-only safety (get_* doesn't mutate)
- Bundle with assets
"""

import pytest
from datetime import datetime, timezone
from aicmo.production.internal.repositories_mem import InMemoryProductionRepo
from aicmo.production.api.dtos import ContentDraftDTO, DraftBundleDTO, AssetDTO


@pytest.fixture
def repo():
    """Fresh in-memory repo for each test."""
    return InMemoryProductionRepo()


@pytest.fixture
def sample_draft():
    """Sample content draft."""
    return ContentDraftDTO(
        draft_id="draft_123",
        strategy_id="strategy_456",
        content_type="blog_post",
        body="# Sample Blog Post\n\nContent here...",
        metadata={"word_count": 1500},
        created_at=datetime(2025, 12, 13, 10, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_bundle(sample_draft):
    """Sample draft bundle with assets."""
    assets = [
        AssetDTO(
            asset_id="asset_img_1",
            asset_type="image",
            url="https://example.com/image.jpg",
            metadata={"width": 1200},
        ),
        AssetDTO(
            asset_id="asset_pdf_1",
            asset_type="pdf",
            url="https://example.com/doc.pdf",
            metadata={"pages": 5},
        ),
    ]
    return DraftBundleDTO(
        bundle_id="bundle_789",
        draft_id=sample_draft.draft_id,
        assets=assets,
        assembled_at=datetime(2025, 12, 13, 11, 0, 0, tzinfo=timezone.utc),
    )


def test_save_and_retrieve_draft(repo, sample_draft):
    """Save draft → retrieve by draft_id → exact match."""
    repo.save_draft(sample_draft)
    
    retrieved = repo.get_draft(sample_draft.draft_id)
    
    assert retrieved is not None
    assert retrieved.draft_id == sample_draft.draft_id
    assert retrieved.strategy_id == sample_draft.strategy_id
    assert retrieved.content_type == sample_draft.content_type
    assert retrieved.body == sample_draft.body
    assert retrieved.metadata == sample_draft.metadata


def test_idempotent_save_draft(repo, sample_draft):
    """Saving same draft_id twice → last write wins (idempotent)."""
    repo.save_draft(sample_draft)
    
    # Save again with different body
    updated_draft = ContentDraftDTO(
        draft_id=sample_draft.draft_id,
        strategy_id=sample_draft.strategy_id,
        content_type="whitepaper",
        body="# Updated Content",
        metadata={"word_count": 2000},
        created_at=sample_draft.created_at,
    )
    repo.save_draft(updated_draft)
    
    retrieved = repo.get_draft(sample_draft.draft_id)
    assert retrieved.content_type == "whitepaper"
    assert retrieved.body == "# Updated Content"


def test_get_nonexistent_draft(repo):
    """Retrieving nonexistent draft_id → None."""
    result = repo.get_draft("nonexistent_draft")
    assert result is None


def test_save_and_retrieve_bundle(repo, sample_bundle):
    """Save bundle with assets → retrieve → exact match."""
    repo.save_bundle(sample_bundle)
    
    retrieved = repo.get_bundle(sample_bundle.bundle_id)
    
    assert retrieved is not None
    assert retrieved.bundle_id == sample_bundle.bundle_id
    assert retrieved.draft_id == sample_bundle.draft_id
    assert len(retrieved.assets) == 2
    assert retrieved.assets[0].asset_id == "asset_img_1"
    assert retrieved.assets[1].asset_id == "asset_pdf_1"


def test_idempotent_save_bundle(repo, sample_bundle):
    """Saving same bundle_id twice → last write wins."""
    repo.save_bundle(sample_bundle)
    
    # Save again with different assets
    new_assets = [
        AssetDTO(
            asset_id="asset_new",
            asset_type="video",
            url="https://example.com/video.mp4",
            metadata={},
        )
    ]
    updated_bundle = DraftBundleDTO(
        bundle_id=sample_bundle.bundle_id,
        draft_id=sample_bundle.draft_id,
        assets=new_assets,
        assembled_at=sample_bundle.assembled_at,
    )
    repo.save_bundle(updated_bundle)
    
    retrieved = repo.get_bundle(sample_bundle.bundle_id)
    assert len(retrieved.assets) == 1
    assert retrieved.assets[0].asset_id == "asset_new"


def test_get_nonexistent_bundle(repo):
    """Retrieving nonexistent bundle_id → None."""
    result = repo.get_bundle("nonexistent_bundle")
    assert result is None


def test_read_only_get_draft(repo, sample_draft):
    """get_draft does not mutate stored state."""
    repo.save_draft(sample_draft)
    
    # Retrieve once
    first_get = repo.get_draft(sample_draft.draft_id)
    
    # Retrieve again (should be identical)
    second_get = repo.get_draft(sample_draft.draft_id)
    
    assert first_get.body == second_get.body
    assert first_get.metadata == second_get.metadata
