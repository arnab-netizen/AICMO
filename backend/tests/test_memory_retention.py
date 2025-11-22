"""
Tests for Phase L memory retention policy.

Covers:
1. Retention limit enforcement
2. Per-project cleanup
3. Memory stats reporting
"""

import pytest
import tempfile
import os

from aicmo.memory.engine import (
    learn_from_blocks,
    _cleanup_old_entries,
    get_memory_stats,
)


@pytest.fixture
def temp_db():
    """Create temporary memory DB for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_memory.db")
        yield db_path


class TestMemoryRetention:
    """Tests for Phase L memory retention policy."""

    def test_learn_from_blocks_basic(self, temp_db):
        """Basic learning should work."""
        blocks = [
            ("Title 1", "Content 1"),
            ("Title 2", "Content 2"),
        ]

        count = learn_from_blocks("report_section", blocks, project_id="test", db_path=temp_db)

        assert count == 2

    def test_memory_stats_after_learning(self, temp_db):
        """Memory stats should reflect learned entries."""
        blocks = [
            ("Section A", "Content A"),
            ("Section B", "Content B"),
            ("Section C", "Content C"),
        ]

        learn_from_blocks("test_kind", blocks, project_id="project1", db_path=temp_db)

        stats = get_memory_stats(temp_db)

        assert stats["total_entries"] == 3
        assert "project1" in stats["entries_per_project"]
        assert stats["entries_per_project"]["project1"] == 3
        assert "test_kind" in stats["top_kinds"]

    def test_cleanup_per_project_limit(self, temp_db):
        """Cleanup should enforce per-project limits."""
        # Set a low limit for testing
        project_id = "test_project"

        # Add more blocks than the limit
        blocks = [(f"Block {i}", f"Content {i}") for i in range(50)]

        count = learn_from_blocks("section", blocks, project_id=project_id, db_path=temp_db)

        assert count == 50

        # Run cleanup with custom limit
        deleted = _cleanup_old_entries(
            temp_db,
            project_id=project_id,
            max_per_project=30,
        )

        # Should have deleted some entries
        assert deleted > 0

        stats = get_memory_stats(temp_db)
        assert stats["entries_per_project"][project_id] <= 30

    def test_cleanup_global_limit(self, temp_db):
        """Cleanup should enforce global limit."""
        # Add entries to multiple projects
        for proj_id in ["p1", "p2", "p3"]:
            blocks = [(f"{proj_id} Block {i}", f"Content {i}") for i in range(100)]
            learn_from_blocks("section", blocks, project_id=proj_id, db_path=temp_db)

        stats_before = get_memory_stats(temp_db)
        initial_count = stats_before["total_entries"]

        # Enforce global limit
        deleted = _cleanup_old_entries(
            temp_db,
            max_total=150,  # Keep only 150 total
        )

        assert deleted > 0

        stats_after = get_memory_stats(temp_db)
        assert stats_after["total_entries"] <= 150
        assert stats_after["total_entries"] < initial_count

    def test_memory_stats_structure(self, temp_db):
        """Memory stats should have expected structure."""
        blocks = [
            ("Test", "Content"),
        ]
        learn_from_blocks("kind1", blocks, project_id="proj1", db_path=temp_db)

        stats = get_memory_stats(temp_db)

        assert "total_entries" in stats
        assert "entries_per_project" in stats
        assert "top_kinds" in stats
        assert "max_per_project" in stats
        assert "max_total" in stats

        assert isinstance(stats["total_entries"], int)
        assert isinstance(stats["entries_per_project"], dict)
        assert isinstance(stats["top_kinds"], dict)

    def test_cleanup_respects_custom_limits(self, temp_db):
        """Cleanup should respect custom limit parameters."""
        # Add blocks
        blocks = [(f"Block {i}", f"Content {i}") for i in range(100)]
        learn_from_blocks("test", blocks, project_id="proj1", db_path=temp_db)

        # Cleanup with strict limits
        _cleanup_old_entries(
            temp_db,
            project_id="proj1",
            max_per_project=10,
            max_total=10,
        )

        stats = get_memory_stats(temp_db)
        assert stats["entries_per_project"]["proj1"] <= 10
        assert stats["total_entries"] <= 10

    def test_multiple_projects_independent(self, temp_db):
        """Different projects should be retained independently."""
        # Add entries to project 1
        blocks1 = [(f"P1 Block {i}", f"Content {i}") for i in range(50)]
        learn_from_blocks("section", blocks1, project_id="project1", db_path=temp_db)

        # Add entries to project 2
        blocks2 = [(f"P2 Block {i}", f"Content {i}") for i in range(30)]
        learn_from_blocks("section", blocks2, project_id="project2", db_path=temp_db)

        # Cleanup project 1 only
        _cleanup_old_entries(
            temp_db,
            project_id="project1",
            max_per_project=20,
        )

        stats = get_memory_stats(temp_db)

        # Project 1 should be limited, project 2 should be unchanged
        assert stats["entries_per_project"]["project1"] <= 20
        assert stats["entries_per_project"]["project2"] == 30

    def test_global_entries_not_lost_on_project_cleanup(self, temp_db):
        """Project cleanup should not affect global entries."""
        # Add global entries
        blocks_global = [(f"Global {i}", f"Content {i}") for i in range(10)]
        learn_from_blocks("section", blocks_global, project_id=None, db_path=temp_db)

        # Add project entries
        blocks_proj = [(f"Proj {i}", f"Content {i}") for i in range(50)]
        learn_from_blocks("section", blocks_proj, project_id="proj1", db_path=temp_db)

        # Cleanup project (should not affect global)
        _cleanup_old_entries(temp_db, project_id="proj1", max_per_project=20)

        final_stats = get_memory_stats(temp_db)

        # Global entries should still be there
        assert "(global)" in final_stats["entries_per_project"]
        assert final_stats["entries_per_project"]["(global)"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
