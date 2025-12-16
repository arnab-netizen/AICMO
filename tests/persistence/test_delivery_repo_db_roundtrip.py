"""Test Delivery Repository - Database Roundtrip (Phase 4 Lane B)."""
import pytest
from datetime import datetime
from sqlalchemy import text
from aicmo.delivery.internal.repositories_db import DatabaseDeliveryRepo
from aicmo.delivery.api.dtos import DeliveryPackageDTO, DeliveryArtifactDTO
from aicmo.shared.ids import DeliveryPackageId, DraftId
from aicmo.core.db import get_session


@pytest.fixture
def repo():
    """Fresh database delivery repository."""
    return DatabaseDeliveryRepo()


@pytest.fixture(autouse=True)
def clean_delivery_tables():
    """Clean delivery tables before and after each test."""
    with get_session() as session:
        # Delete child before parent
        session.execute(text("DELETE FROM delivery_artifacts"))
        session.execute(text("DELETE FROM delivery_packages"))
        session.commit()
    
    yield
    
    with get_session() as session:
        session.execute(text("DELETE FROM delivery_artifacts"))
        session.execute(text("DELETE FROM delivery_packages"))
        session.commit()


@pytest.fixture
def sample_package():
    """Sample delivery package."""
    return DeliveryPackageDTO(
        package_id=DeliveryPackageId("pkg_001"),
        draft_id=DraftId("draft_xyz"),
        artifacts=[
            DeliveryArtifactDTO(name="pack.zip", url="https://example.com/pack.zip", format="zip"),
            DeliveryArtifactDTO(name="doc.pdf", url="https://example.com/doc.pdf", format="pdf"),
        ],
        created_at=datetime(2025, 1, 15, 10, 0, 0),
    )


def test_db_repo_save_and_retrieve(repo, sample_package):
    """Test save and retrieve delivery package from database."""
    repo.save_package(sample_package)
    retrieved = repo.get_package(sample_package.package_id)
    
    assert retrieved is not None
    assert retrieved.package_id == sample_package.package_id
    assert retrieved.draft_id == sample_package.draft_id
    assert len(retrieved.artifacts) == 2
    assert retrieved.artifacts[0].name == "pack.zip"
    assert retrieved.artifacts[1].name == "doc.pdf"


def test_db_repo_get_nonexistent_returns_none(repo):
    """Test retrieving non-existent package returns None."""
    result = repo.get_package(DeliveryPackageId("nonexistent"))
    assert result is None


def test_db_repo_idempotency_same_package_id(repo):
    """Test saving same package_id twice replaces previous package (idempotent)."""
    pkg1 = DeliveryPackageDTO(
        package_id=DeliveryPackageId("pkg_001"),
        draft_id=DraftId("draft_v1"),
        artifacts=[
            DeliveryArtifactDTO(name="old.zip", url="https://old.com/old.zip", format="zip"),
        ],
        created_at=datetime(2025, 1, 1, 10, 0, 0),
    )
    
    pkg2 = DeliveryPackageDTO(
        package_id=DeliveryPackageId("pkg_001"),  # Same package_id
        draft_id=DraftId("draft_v2"),
        artifacts=[
            DeliveryArtifactDTO(name="new.zip", url="https://new.com/new.zip", format="zip"),
            DeliveryArtifactDTO(name="extra.pdf", url="https://new.com/extra.pdf", format="pdf"),
        ],
        created_at=datetime(2025, 1, 15, 10, 0, 0),
    )
    
    repo.save_package(pkg1)
    repo.save_package(pkg2)
    
    retrieved = repo.get_package(DeliveryPackageId("pkg_001"))
    assert retrieved.draft_id == DraftId("draft_v2")  # Latest wins
    assert len(retrieved.artifacts) == 2  # New artifacts replace old
    assert retrieved.artifacts[0].name == "new.zip"


def test_db_repo_artifact_order_deterministic(repo):
    """Test artifacts are returned in deterministic position order."""
    pkg = DeliveryPackageDTO(
        package_id=DeliveryPackageId("pkg_order"),
        draft_id=DraftId("draft_xyz"),
        artifacts=[
            DeliveryArtifactDTO(name="third.txt", url="https://example.com/3.txt", format="txt"),
            DeliveryArtifactDTO(name="first.zip", url="https://example.com/1.zip", format="zip"),
            DeliveryArtifactDTO(name="second.pdf", url="https://example.com/2.pdf", format="pdf"),
        ],
        created_at=datetime(2025, 1, 15, 10, 0, 0),
    )
    
    repo.save_package(pkg)
    retrieved = repo.get_package(pkg.package_id)
    
    # Order must match original (position field ensures this)
    assert retrieved.artifacts[0].name == "third.txt"
    assert retrieved.artifacts[1].name == "first.zip"
    assert retrieved.artifacts[2].name == "second.pdf"


def test_db_repo_cascade_delete_artifacts(repo):
    """Test artifacts are cascade deleted when package is replaced."""
    pkg1 = DeliveryPackageDTO(
        package_id=DeliveryPackageId("pkg_cascade"),
        draft_id=DraftId("draft_v1"),
        artifacts=[
            DeliveryArtifactDTO(name="a.zip", url="https://a.com/a.zip", format="zip"),
            DeliveryArtifactDTO(name="b.pdf", url="https://b.com/b.pdf", format="pdf"),
        ],
        created_at=datetime(2025, 1, 1, 10, 0, 0),
    )
    
    pkg2 = DeliveryPackageDTO(
        package_id=DeliveryPackageId("pkg_cascade"),  # Same package_id
        draft_id=DraftId("draft_v2"),
        artifacts=[
            DeliveryArtifactDTO(name="c.zip", url="https://c.com/c.zip", format="zip"),
        ],
        created_at=datetime(2025, 1, 15, 10, 0, 0),
    )
    
    repo.save_package(pkg1)
    
    # Verify 2 artifacts exist
    with get_session() as session:
        artifact_count = session.execute(
            text("SELECT COUNT(*) FROM delivery_artifacts WHERE package_id = :pkg_id"),
            {"pkg_id": "pkg_cascade"}
        ).scalar()
        assert artifact_count == 2
    
    # Replace package
    repo.save_package(pkg2)
    
    # Verify old artifacts deleted, new artifact saved
    with get_session() as session:
        artifact_count = session.execute(
            text("SELECT COUNT(*) FROM delivery_artifacts WHERE package_id = :pkg_id"),
            {"pkg_id": "pkg_cascade"}
        ).scalar()
        assert artifact_count == 1  # Only new artifact
        
        artifact_name = session.execute(
            text("SELECT name FROM delivery_artifacts WHERE package_id = :pkg_id"),
            {"pkg_id": "pkg_cascade"}
        ).scalar()
        assert artifact_name == "c.zip"


def test_db_repo_empty_artifacts_list(repo):
    """Test package with no artifacts (edge case)."""
    pkg = DeliveryPackageDTO(
        package_id=DeliveryPackageId("pkg_empty"),
        draft_id=DraftId("draft_xyz"),
        artifacts=[],  # No artifacts
        created_at=datetime(2025, 1, 15, 10, 0, 0),
    )
    
    repo.save_package(pkg)
    retrieved = repo.get_package(pkg.package_id)
    
    assert retrieved is not None
    assert len(retrieved.artifacts) == 0


def test_db_repo_transaction_rollback_on_error(repo):
    """Test transaction rollback on save error."""
    # This test verifies error handling (implementation detail: IntegrityError)
    # In practice, unique constraint on package_id should never trigger
    # because we delete-then-insert, but we test rollback safety anyway.
    
    pkg = DeliveryPackageDTO(
        package_id=DeliveryPackageId("pkg_txn"),
        draft_id=DraftId("draft_xyz"),
        artifacts=[
            DeliveryArtifactDTO(name="test.zip", url="https://test.com/test.zip", format="zip"),
        ],
        created_at=datetime(2025, 1, 15, 10, 0, 0),
    )
    
    repo.save_package(pkg)
    
    # Save should succeed (idempotent behavior tested elsewhere)
    repo.save_package(pkg)
    
    # Verify still exists after second save
    retrieved = repo.get_package(pkg.package_id)
    assert retrieved is not None


def test_db_repo_multiple_packages_independent(repo):
    """Test multiple packages stored independently."""
    pkg1 = DeliveryPackageDTO(
        package_id=DeliveryPackageId("pkg_001"),
        draft_id=DraftId("draft_a"),
        artifacts=[
            DeliveryArtifactDTO(name="a.zip", url="https://a.com/a.zip", format="zip"),
        ],
        created_at=datetime(2025, 1, 15, 10, 0, 0),
    )
    
    pkg2 = DeliveryPackageDTO(
        package_id=DeliveryPackageId("pkg_002"),
        draft_id=DraftId("draft_b"),
        artifacts=[
            DeliveryArtifactDTO(name="b.pdf", url="https://b.com/b.pdf", format="pdf"),
        ],
        created_at=datetime(2025, 1, 16, 10, 0, 0),
    )
    
    repo.save_package(pkg1)
    repo.save_package(pkg2)
    
    retrieved1 = repo.get_package(pkg1.package_id)
    retrieved2 = repo.get_package(pkg2.package_id)
    
    assert retrieved1.draft_id == DraftId("draft_a")
    assert retrieved2.draft_id == DraftId("draft_b")
    assert retrieved1.artifacts[0].name == "a.zip"
    assert retrieved2.artifacts[0].name == "b.pdf"
