"""
Test Phase 0: Skeleton structure verification.

Ensures that new aicmo/* modules are importable and that domain models
work correctly without breaking existing backend behavior.
"""

import pytest


class TestPhase0Skeleton:
    """Verify Phase 0 skeleton structure."""

    def test_domain_models_importable(self):
        """All domain models should import without errors."""
        from aicmo.domain import (
            AicmoBaseModel,
            ClientIntake,
            GoalMetric,
            StrategyDoc,
            StrategyStatus,
            Project,
            ProjectState,
            ContentItem,
            PublishStatus,
        )

        assert AicmoBaseModel is not None
        assert ClientIntake is not None
        assert GoalMetric is not None
        assert StrategyDoc is not None
        assert StrategyStatus is not None
        assert Project is not None
        assert ProjectState is not None
        assert ContentItem is not None
        assert PublishStatus is not None

    def test_core_imports(self):
        """Core infrastructure should be accessible."""
        from aicmo.core import settings, Base

        assert settings is not None
        assert Base is not None

    def test_client_intake_from_dict(self):
        """ClientIntake should adapt from dict correctly."""
        from aicmo.domain import ClientIntake

        data = {
            "brand_name": "Test Co",
            "industry": "Technology",
            "primary_goal": "Increase awareness",
        }

        intake = ClientIntake.from_existing_request(data)
        assert intake.brand_name == "Test Co"
        assert intake.industry == "Technology"
        assert intake.primary_goal_description == "Increase awareness"

    def test_strategy_doc_from_dict(self):
        """StrategyDoc should adapt from dict correctly."""
        from aicmo.domain import StrategyDoc, StrategyStatus

        data = {
            "title": "Q4 Strategy",
            "summary": "Focus on digital channels",
            "extra_field": "value",
        }

        doc = StrategyDoc.from_existing_response(data)
        assert doc.title == "Q4 Strategy"
        assert doc.summary == "Focus on digital channels"
        assert doc.status == StrategyStatus.DRAFT
        assert doc.raw_payload["extra_field"] == "value"

    def test_project_states_enum(self):
        """Project states should be valid enum values."""
        from aicmo.domain import ProjectState

        assert ProjectState.NEW_LEAD.value == "NEW_LEAD"
        assert ProjectState.STRATEGY_DRAFT.value == "STRATEGY_DRAFT"
        assert ProjectState.EXECUTION_DONE.value == "EXECUTION_DONE"

    def test_content_item_publish_status(self):
        """ContentItem should track publish status."""
        from aicmo.domain import ContentItem, PublishStatus

        item = ContentItem(
            platform="linkedin",
            body_text="Test post content",
            publish_status=PublishStatus.DRAFT,
        )

        assert item.platform == "linkedin"
        assert item.publish_status == PublishStatus.DRAFT
        assert item.external_id is None

    def test_strategy_service_not_implemented(self):
        """Strategy service should raise NotImplementedError in Phase 0."""
        from aicmo.strategy import generate_strategy
        from aicmo.domain import ClientIntake

        intake = ClientIntake(brand_name="Test")

        with pytest.raises(NotImplementedError, match="Implement in Phase 1"):
            generate_strategy(intake)

    def test_no_backend_imports_aicmo_new_modules(self):
        """
        Verify no existing backend code imports from new aicmo modules.
        This ensures Phase 0 doesn't break existing functionality.
        """
        import subprocess

        # Search for imports in backend files (exclude test files)
        result = subprocess.run(
            [
                "grep",
                "-r",
                "-E",
                r"from aicmo\.(domain|core|strategy|creatives|delivery|gateways|acquisition|cam)",
                "backend/",
                "--exclude-dir=tests",
            ],
            cwd="/workspaces/AICMO",
            capture_output=True,
            text=True,
        )

        # Should have no matches (exit code 1 means no matches found)
        assert result.returncode == 1, f"Found backend imports from new aicmo modules:\n{result.stdout}"


# Test command to run:
# PYTHONPATH=/workspaces/AICMO pytest backend/tests/test_phase0_skeleton.py -v
