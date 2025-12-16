"""Test Delivery Repository - Parity (mem vs db) (Phase 4 Lane B)."""
import pytest
from datetime import datetime
from sqlalchemy import text
from aicmo.delivery.internal.repositories_mem import InMemoryDeliveryRepo
from aicmo.delivery.internal.repositories_db import DatabaseDeliveryRepo
from aicmo.delivery.api.dtos import DeliveryPackageDTO, DeliveryArtifactDTO
from aicmo.shared.ids import DeliveryPackageId, DraftId
from aicmo.core.db import get_session
from tests.persistence._canon import canonicalize_delivery_package


@pytest.fixture
def mem_repo():
    """Fresh in-memory delivery repository."""
    return InMemoryDeliveryRepo()


@pytest.fixture
def db_repo():
    """Fresh database delivery repository."""
    return DatabaseDeliveryRepo()


@pytest.fixture(autouse=True)
def clean_delivery_tables():
    """Clean delivery tables before and after each test."""
    with get_session() as session:
        session.execute(text("DELETE FROM delivery_artifacts"))
        session.execute(text("DELETE FROM delivery_packages"))
        session.commit()
    
    yield
    
    with get_session() as session:
        session.execute(text("DELETE FROM delivery_artifacts"))
        session.execute(text("DELETE FROM delivery_packages"))
        session.commit()


def test_parity_basic_package_with_artifacts(mem_repo, db_repo):
    """Test mem and db repos produce identical output for basic package."""
    pkg = DeliveryPackageDTO(
        package_id=DeliveryPackageId("pkg_001"),
        draft_id=DraftId("draft_xyz"),
        artifacts=[
            DeliveryArtifactDTO(name="pack.zip", url="https://example.com/pack.zip", format="zip"),
            DeliveryArtifactDTO(name="doc.pdf", url="https://example.com/doc.pdf", format="pdf"),
        ],
        created_at=datetime(2025, 1, 15, 10, 0, 0),
    )
    
    mem_repo.save_package(pkg)
    db_repo.save_package(pkg)
    
    mem_result = mem_repo.get_package(pkg.package_id)
    db_result = db_repo.get_package(pkg.package_id)
    
    assert canonicalize_delivery_package(mem_result) == canonicalize_delivery_package(db_result)


def test_parity_idempotency_behavior(mem_repo, db_repo):
    """Test mem and db repos have identical idempotency semantics."""
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
    
    # Save pkg1, then pkg2 (same package_id)
    mem_repo.save_package(pkg1)
    db_repo.save_package(pkg1)
    
    mem_repo.save_package(pkg2)
    db_repo.save_package(pkg2)
    
    mem_result = mem_repo.get_package(DeliveryPackageId("pkg_001"))
    db_result = db_repo.get_package(DeliveryPackageId("pkg_001"))
    
    # Both should have pkg2 data (latest wins)
    assert canonicalize_delivery_package(mem_result) == canonicalize_delivery_package(db_result)
    assert mem_result.draft_id == DraftId("draft_v2")
    assert db_result.draft_id == DraftId("draft_v2")
    assert len(mem_result.artifacts) == 2
    assert len(db_result.artifacts) == 2


def test_parity_artifact_ordering_preserved(mem_repo, db_repo):
    """Test mem and db repos maintain identical artifact order."""
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
    
    mem_repo.save_package(pkg)
    db_repo.save_package(pkg)
    
    mem_result = mem_repo.get_package(pkg.package_id)
    db_result = db_repo.get_package(pkg.package_id)
    
    # Canonicalized comparison
    assert canonicalize_delivery_package(mem_result) == canonicalize_delivery_package(db_result)
    
    # Explicit order check
    for i in range(3):
        assert mem_result.artifacts[i].name == db_result.artifacts[i].name


def test_parity_empty_artifacts_list(mem_repo, db_repo):
    """Test mem and db repos handle empty artifact lists identically."""
    pkg = DeliveryPackageDTO(
        package_id=DeliveryPackageId("pkg_empty"),
        draft_id=DraftId("draft_xyz"),
        artifacts=[],  # No artifacts
        created_at=datetime(2025, 1, 15, 10, 0, 0),
    )
    
    mem_repo.save_package(pkg)
    db_repo.save_package(pkg)
    
    mem_result = mem_repo.get_package(pkg.package_id)
    db_result = db_repo.get_package(pkg.package_id)
    
    assert canonicalize_delivery_package(mem_result) == canonicalize_delivery_package(db_result)
    assert len(mem_result.artifacts) == 0
    assert len(db_result.artifacts) == 0


def test_parity_nonexistent_package_returns_none(mem_repo, db_repo):
    """Test mem and db repos both return None for non-existent package."""
    mem_result = mem_repo.get_package(DeliveryPackageId("nonexistent"))
    db_result = db_repo.get_package(DeliveryPackageId("nonexistent"))
    
    assert mem_result is None
    assert db_result is None
