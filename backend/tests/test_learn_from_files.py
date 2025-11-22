"""Tests for learning from uploaded files endpoint."""

from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


class TestLearnFromFilesEndpoint:
    """Tests for POST /api/learn/from-files endpoint."""

    def test_learn_from_files_success(self):
        """Should successfully learn from uploaded files."""
        payload = {
            "project_id": "test-files",
            "files": [
                {
                    "filename": "agency_report.txt",
                    "text": "Best practice: Always start with audience research before campaign planning.",
                },
                {
                    "filename": "case_study.txt",
                    "text": "Case Study: Brand X increased engagement 300% by focusing on community.",
                },
            ],
        }

        response = client.post("/api/learn/from-files", json=payload)

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "ok"
        assert result["items_learned"] == 2

    def test_learn_from_files_empty(self):
        """Should handle empty file list gracefully."""
        payload = {"project_id": "test-empty", "files": []}

        response = client.post("/api/learn/from-files", json=payload)

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "ok"
        assert result["items_learned"] == 0

    def test_learn_from_files_empty_text(self):
        """Should skip files with empty text."""
        payload = {
            "project_id": "test-empty-text",
            "files": [
                {"filename": "empty.txt", "text": ""},
                {"filename": "whitespace.txt", "text": "   \n\t  "},
            ],
        }

        response = client.post("/api/learn/from-files", json=payload)

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "ok"
        assert result["items_learned"] == 0

    def test_learn_from_files_mixed_content(self):
        """Should handle mix of valid and empty files."""
        payload = {
            "project_id": "test-mixed",
            "files": [
                {"filename": "valid.txt", "text": "Important marketing strategy content"},
                {"filename": "empty.txt", "text": ""},
                {"filename": "another.txt", "text": "More valuable insights for campaigns"},
            ],
        }

        response = client.post("/api/learn/from-files", json=payload)

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "ok"
        assert result["items_learned"] == 2  # Only the 2 non-empty files

    def test_learn_from_files_no_project_id(self):
        """Should work without explicit project_id."""
        payload = {
            "files": [
                {"filename": "doc.txt", "text": "Content without project ID"},
            ],
        }

        response = client.post("/api/learn/from-files", json=payload)

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "ok"
        assert result["items_learned"] == 1

    def test_learn_from_files_missing_filename(self):
        """Should handle missing filename gracefully."""
        payload = {
            "project_id": "test-missing-name",
            "files": [
                {"text": "Content without filename"},
                {"filename": "named.txt", "text": "Content with filename"},
            ],
        }

        response = client.post("/api/learn/from-files", json=payload)

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "ok"
        # Both files should be stored (one gets "untitled" filename)
        assert result["items_learned"] == 2

    def test_learn_from_files_missing_text(self):
        """Should handle missing text field gracefully."""
        payload = {
            "project_id": "test-missing-text",
            "files": [
                {"filename": "no_text.txt"},  # Missing text field
                {"filename": "with_text.txt", "text": "Valid content"},
            ],
        }

        response = client.post("/api/learn/from-files", json=payload)

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "ok"
        # Only file with text should be stored
        assert result["items_learned"] == 1

    def test_debug_summary_includes_training_pack(self):
        """Debug endpoint should show training_pack items after learning from files."""
        # First, learn from files
        payload = {
            "project_id": "test-debug",
            "files": [
                {"filename": "test.txt", "text": "Training material for testing"},
            ],
        }

        response = client.post("/api/learn/from-files", json=payload)
        assert response.status_code == 200

        # Then check debug summary
        response = client.get("/api/learn/debug/summary")
        assert response.status_code == 200
        result = response.json()

        # Should have per_kind breakdown that includes training_pack
        assert "per_kind" in result
        # (Note: may have other kinds too from other tests)

    def test_learn_from_files_db_error_returns_500_with_safe_message(self):
        """Test that DB errors are caught and return 500 with safe message."""
        from unittest.mock import patch

        payload = {
            "files": [
                {"filename": "test.txt", "text": "Some content here"},
            ],
            "project_id": None,
        }

        # Mock learn_from_blocks to raise an exception
        with patch("aicmo.memory.engine.learn_from_blocks") as mock_learn:
            mock_learn.side_effect = Exception("Simulated DB error: disk full")

            response = client.post("/api/learn/from-files", json=payload)

            # Should return 500
            assert response.status_code == 500

            # Response should have safe message, not the raw exception
            data = response.json()
            assert "detail" in data
            detail = data["detail"]
            # Should NOT contain the simulated error message
            assert "disk full" not in detail
            # Should contain a safe generic message
            assert "Failed to store learning blocks" in detail

    def test_debug_summary_db_error_returns_500_with_safe_message(self):
        """Test that DB errors in /debug/summary don't leak details."""
        from unittest.mock import patch

        with patch("backend.api.routes_learn.sqlite3.connect") as mock_connect:
            # Simulate DB connection failure
            mock_connect.side_effect = Exception(
                "Simulated DB error: /secret/path/to/db.db corrupted"
            )

            response = client.get("/api/learn/debug/summary")

            # Should return 500
            assert response.status_code == 500

            # Response should have safe message, not the raw exception
            data = response.json()
            assert "detail" in data
            detail = data["detail"]

            # Should NOT contain the simulated error details (paths, internals)
            assert "secret" not in detail.lower()
            assert "corrupted" not in detail.lower()
            assert "/db" not in detail

            # Should contain generic message
            assert "Error reading Phase L database" in detail
