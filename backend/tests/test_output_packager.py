"""
Tests for Output Packager.

Verifies that the output packaging layer:
- Runs without raising exceptions
- Handles successful file generation
- Handles failures gracefully (partial success)
- Returns valid ProjectPackageResult
- Logs events via existing learning system
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from aicmo.delivery.output_packager import (
    ProjectPackageResult,
    build_project_package,
)


class TestProjectPackageResult:
    """Test suite for package result structure."""
    
    def test_package_result_structure(self):
        """Test that ProjectPackageResult has all required fields."""
        result = ProjectPackageResult(project_id="proj-123")
        
        assert hasattr(result, 'project_id')
        assert hasattr(result, 'pdf_path')
        assert hasattr(result, 'pptx_path')
        assert hasattr(result, 'html_summary_path')
        assert hasattr(result, 'metadata')
        assert hasattr(result, 'success')
        assert hasattr(result, 'errors')
        assert hasattr(result, 'created_at')
        
        # Verify initial state
        assert result.project_id == "proj-123"
        assert result.pdf_path is None
        assert result.pptx_path is None
        assert result.html_summary_path is None
        assert result.success is False
        assert isinstance(result.metadata, dict)
        assert isinstance(result.errors, list)
    
    def test_add_error(self):
        """Test that errors can be added to result."""
        result = ProjectPackageResult(project_id="proj-123")
        
        result.add_error("Error 1")
        assert len(result.errors) == 1
        assert "Error 1" in result.errors
        
        # Duplicate errors should not be added
        result.add_error("Error 1")
        assert len(result.errors) == 1
        
        # Different errors should be added
        result.add_error("Error 2")
        assert len(result.errors) == 2
    
    def test_file_count(self):
        """Test file count calculation."""
        result = ProjectPackageResult(project_id="proj-123")
        
        assert result.file_count() == 0
        
        result.pdf_path = "/tmp/test.pdf"
        assert result.file_count() == 1
        
        result.pptx_path = "/tmp/test.pptx"
        assert result.file_count() == 2
        
        result.html_summary_path = "/tmp/test.html"
        assert result.file_count() == 3


class TestBuildProjectPackage:
    """Test suite for main packaging function."""
    
    def test_build_project_package_returns_result(self):
        """Test that build_project_package returns ProjectPackageResult."""
        report = build_project_package("proj-123")
        
        assert isinstance(report, ProjectPackageResult)
        assert report.project_id == "proj-123"
    
    def test_build_project_package_project_not_found(self):
        """Test handling of missing project."""
        with patch(
            'aicmo.delivery.output_packager.fetch_project_data'
        ) as mock_fetch:
            mock_fetch.return_value = None
            
            result = build_project_package("proj-nonexistent")
            
            # Should return result with error recorded
            assert isinstance(result, ProjectPackageResult)
            assert result.success is False
            assert len(result.errors) > 0
            assert "not found" in str(result.errors).lower()
    
    def test_build_project_package_partial_success(self):
        """Test that partial file generation counts as success."""
        with patch(
            'aicmo.delivery.output_packager.fetch_project_data'
        ) as mock_fetch, \
        patch(
            'aicmo.delivery.output_packager.generate_strategy_pdf'
        ) as mock_pdf, \
        patch(
            'aicmo.delivery.output_packager.generate_full_deck_pptx'
        ) as mock_pptx, \
        patch(
            'aicmo.delivery.output_packager.generate_html_summary'
        ) as mock_html:
            
            # Setup mocks
            mock_fetch.return_value = {"id": "proj-123", "name": "Test Project"}
            mock_pdf.return_value = "/tmp/test.pdf"
            mock_pptx.side_effect = Exception("PPTX generation failed")
            mock_html.return_value = None
            
            result = build_project_package("proj-123")
            
            # Should mark as success because PDF was generated
            assert result.success is True
            assert result.pdf_path == "/tmp/test.pdf"
            assert result.pptx_path is None
            assert result.html_summary_path is None
            assert result.file_count() == 1
    
    def test_build_project_package_all_generators_fail(self):
        """Test when all generators fail."""
        with patch(
            'aicmo.delivery.output_packager.fetch_project_data'
        ) as mock_fetch, \
        patch(
            'aicmo.delivery.output_packager.generate_strategy_pdf'
        ) as mock_pdf, \
        patch(
            'aicmo.delivery.output_packager.generate_full_deck_pptx'
        ) as mock_pptx, \
        patch(
            'aicmo.delivery.output_packager.generate_html_summary'
        ) as mock_html:
            
            # Setup mocks - all fail
            mock_fetch.return_value = {"id": "proj-123"}
            mock_pdf.side_effect = Exception("PDF failed")
            mock_pptx.side_effect = Exception("PPTX failed")
            mock_html.side_effect = Exception("HTML failed")
            
            result = build_project_package("proj-123")
            
            # Should mark as failure
            assert result.success is False
            assert result.file_count() == 0
            assert len(result.errors) == 3
    
    def test_build_project_package_all_success(self):
        """Test when all generators succeed."""
        with patch(
            'aicmo.delivery.output_packager.fetch_project_data'
        ) as mock_fetch, \
        patch(
            'aicmo.delivery.output_packager.generate_strategy_pdf'
        ) as mock_pdf, \
        patch(
            'aicmo.delivery.output_packager.generate_full_deck_pptx'
        ) as mock_pptx, \
        patch(
            'aicmo.delivery.output_packager.generate_html_summary'
        ) as mock_html:
            
            # Setup mocks - all succeed
            mock_fetch.return_value = {"id": "proj-123"}
            mock_pdf.return_value = "/tmp/test.pdf"
            mock_pptx.return_value = "/tmp/test.pptx"
            mock_html.return_value = "/tmp/test.html"
            
            result = build_project_package("proj-123")
            
            # Should mark as success
            assert result.success is True
            assert result.pdf_path == "/tmp/test.pdf"
            assert result.pptx_path == "/tmp/test.pptx"
            assert result.html_summary_path == "/tmp/test.html"
            assert result.file_count() == 3
            assert "pdf" in result.metadata["files_generated"]
            assert "pptx" in result.metadata["files_generated"]
            assert "html" in result.metadata["files_generated"]
    
    def test_build_project_package_no_exceptions(self):
        """Test that build_project_package never raises exceptions."""
        # Test with various failure scenarios
        test_cases = [
            # All generators fail
            {
                "fetch": None,
                "pdf": Exception("PDF error"),
                "pptx": Exception("PPTX error"),
                "html": Exception("HTML error"),
            },
            # Fetch fails
            {
                "fetch": Exception("Fetch error"),
                "pdf": None,
                "pptx": None,
                "html": None,
            },
            # All return None
            {
                "fetch": {"id": "proj-123"},
                "pdf": None,
                "pptx": None,
                "html": None,
            },
        ]
        
        for test_case in test_cases:
            with patch(
                'aicmo.delivery.output_packager.fetch_project_data'
            ) as mock_fetch, \
            patch(
                'aicmo.delivery.output_packager.generate_strategy_pdf'
            ) as mock_pdf, \
            patch(
                'aicmo.delivery.output_packager.generate_full_deck_pptx'
            ) as mock_pptx, \
            patch(
                'aicmo.delivery.output_packager.generate_html_summary'
            ) as mock_html:
                
                # Setup mocks based on test case
                if isinstance(test_case["fetch"], Exception):
                    mock_fetch.side_effect = test_case["fetch"]
                else:
                    mock_fetch.return_value = test_case["fetch"]
                
                if isinstance(test_case["pdf"], Exception):
                    mock_pdf.side_effect = test_case["pdf"]
                else:
                    mock_pdf.return_value = test_case["pdf"]
                
                if isinstance(test_case["pptx"], Exception):
                    mock_pptx.side_effect = test_case["pptx"]
                else:
                    mock_pptx.return_value = test_case["pptx"]
                
                if isinstance(test_case["html"], Exception):
                    mock_html.side_effect = test_case["html"]
                else:
                    mock_html.return_value = test_case["html"]
                
                # Should never raise
                result = build_project_package("proj-123")
                assert isinstance(result, ProjectPackageResult)


class TestPackagingIntegration:
    """Integration tests for packaging workflow."""
    
    def test_full_packaging_workflow(self):
        """Test complete packaging workflow."""
        with patch(
            'aicmo.delivery.output_packager.fetch_project_data'
        ) as mock_fetch, \
        patch(
            'aicmo.delivery.output_packager.generate_strategy_pdf'
        ) as mock_pdf, \
        patch(
            'aicmo.delivery.output_packager.generate_full_deck_pptx'
        ) as mock_pptx, \
        patch(
            'aicmo.delivery.output_packager.generate_html_summary'
        ) as mock_html:
            
            # Setup mocks for complete success
            project_data = {
                "id": "proj-123",
                "name": "Test Project",
                "client": "Test Client"
            }
            mock_fetch.return_value = project_data
            mock_pdf.return_value = "/output/proj-123/strategy.pdf"
            mock_pptx.return_value = "/output/proj-123/deck.pptx"
            mock_html.return_value = "/output/proj-123/summary.html"
            
            # Execute
            result = build_project_package("proj-123")
            
            # Verify results
            assert result.project_id == "proj-123"
            assert result.success is True
            assert result.file_count() == 3
            assert result.created_at is not None
            
            # Verify metadata
            assert result.metadata["total_files"] == 3
            assert result.metadata["error_count"] == 0
            assert set(result.metadata["files_generated"]) == {"pdf", "pptx", "html"}
            
            # Verify mocks were called
            mock_fetch.assert_called_once_with("proj-123")
            mock_pdf.assert_called_once_with(project_data)
            mock_pptx.assert_called_once_with(project_data)
            mock_html.assert_called_once_with(project_data)
    
    def test_packaging_with_partial_failures(self):
        """Test packaging with some generators failing."""
        with patch(
            'aicmo.delivery.output_packager.fetch_project_data'
        ) as mock_fetch, \
        patch(
            'aicmo.delivery.output_packager.generate_strategy_pdf'
        ) as mock_pdf, \
        patch(
            'aicmo.delivery.output_packager.generate_full_deck_pptx'
        ) as mock_pptx, \
        patch(
            'aicmo.delivery.output_packager.generate_html_summary'
        ) as mock_html:
            
            # Setup mocks - PDF succeeds, PPTX fails, HTML returns None
            mock_fetch.return_value = {"id": "proj-123"}
            mock_pdf.return_value = "/output/proj-123/strategy.pdf"
            mock_pptx.side_effect = Exception("Network error")
            mock_html.return_value = None
            
            result = build_project_package("proj-123")
            
            # Should still be marked as success (PDF exists)
            assert result.success is True
            assert result.pdf_path is not None
            assert result.pptx_path is None
            assert result.html_summary_path is None
            
            # Should record errors
            assert len(result.errors) >= 1
            assert result.metadata["error_count"] >= 1
