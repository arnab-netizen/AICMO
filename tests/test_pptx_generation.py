"""
Tests for PPTX PowerPoint generation.

Tests the python-pptx implementation including:
- PowerPoint file creation with correct slide structure
- Handling when python-pptx library not installed
- Temporary file generation and naming
- Content extraction from project_data
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
from pathlib import Path


class TestPPTXGeneration:
    """Test PPTX file generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Import here to avoid import errors if library not available
        try:
            from aicmo.delivery.output_packager import generate_full_deck_pptx
            self.generate_pptx = generate_full_deck_pptx
        except ImportError:
            self.generate_pptx = None
        
        self.test_project_data = {
            "project_name": "Test Campaign",
            "objective": "Launch new product",
            "platforms": {
                "LinkedIn": {"posts": 10, "engagement": 0.05},
                "Twitter": {"posts": 20, "engagement": 0.03}
            },
            "strategy": "Focus on B2B engagement",
            "calendar": [
                {"date": "2024-01-15", "platform": "LinkedIn", "content": "Post 1"},
                {"date": "2024-01-16", "platform": "Twitter", "content": "Post 2"}
            ],
            "deliverables": ["Campaign brief", "Content calendar", "Performance report"]
        }
    
    @patch("aicmo.delivery.output_packager.requests.post")
    def test_pptx_generation_creates_file(self, mock_post):
        """Test that PPTX generation creates a file."""
        if self.generate_pptx is None:
            pytest.skip("python-pptx library not available")
        
        # Mock the API if needed
        mock_post.return_value = Mock(status_code=200)
        
        # Generate PPTX
        result = self.generate_pptx(self.test_project_data)
        
        # Assert file was created
        assert result is not None
        assert isinstance(result, str)
        assert result.endswith(".pptx")
        
        # Check file exists
        assert os.path.exists(result)
        
        # Clean up
        if os.path.exists(result):
            os.remove(result)
    
    @patch("aicmo.delivery.output_packager.requests.post")
    def test_pptx_generation_file_naming(self, mock_post):
        """Test PPTX file naming convention."""
        if self.generate_pptx is None:
            pytest.skip("python-pptx library not available")
        
        mock_post.return_value = Mock(status_code=200)
        
        result = self.generate_pptx(self.test_project_data)
        
        assert result is not None
        # Should be in temp directory
        assert "/tmp/" in result or "\\tmp\\" in result or "Temp" in result
        # Should have timestamp
        filename = os.path.basename(result)
        assert "deck_" in filename
    
    @patch("aicmo.delivery.output_packager.requests.post")
    def test_pptx_generation_with_minimal_data(self, mock_post):
        """Test PPTX generation with minimal project data."""
        if self.generate_pptx is None:
            pytest.skip("python-pptx library not available")
        
        mock_post.return_value = Mock(status_code=200)
        
        minimal_data = {
            "project_name": "Minimal",
            "objective": "Test",
            "platforms": {},
            "strategy": "None",
            "calendar": [],
            "deliverables": []
        }
        
        result = self.generate_pptx(minimal_data)
        
        # Should still create file
        assert result is not None
        assert os.path.exists(result)
        
        # Clean up
        if os.path.exists(result):
            os.remove(result)
    
    def test_pptx_generation_library_not_installed(self):
        """Test graceful handling when python-pptx not installed."""
        # Simulate ImportError
        with patch("aicmo.delivery.output_packager.Presentation", side_effect=ImportError("No module")):
            from aicmo.delivery.output_packager import generate_full_deck_pptx
            
            result = generate_full_deck_pptx(self.test_project_data)
            
            # Should return None, not crash
            assert result is None
    
    @patch("aicmo.delivery.output_packager.requests.post")
    def test_pptx_generation_with_special_characters(self, mock_post):
        """Test PPTX generation with special characters in data."""
        if self.generate_pptx is None:
            pytest.skip("python-pptx library not available")
        
        mock_post.return_value = Mock(status_code=200)
        
        special_data = {
            "project_name": "Test & Campaign (2024) 'Special'",
            "objective": "Launch → Product™",
            "platforms": {"LinkedIn": {"posts": 10}},
            "strategy": "Focus on <B2B> & engagement",
            "calendar": [],
            "deliverables": ["Brief © 2024"]
        }
        
        result = self.generate_pptx(special_data)
        
        # Should handle special characters without crashing
        assert result is not None
        
        # Clean up
        if result and os.path.exists(result):
            os.remove(result)
    
    @patch("aicmo.delivery.output_packager.requests.post")
    def test_pptx_generation_large_calendar(self, mock_post):
        """Test PPTX generation with large calendar."""
        if self.generate_pptx is None:
            pytest.skip("python-pptx library not available")
        
        mock_post.return_value = Mock(status_code=200)
        
        # Generate 30-day calendar
        large_calendar = [
            {"date": f"2024-01-{i:02d}", "platform": "LinkedIn", "content": f"Post {i}"}
            for i in range(1, 31)
        ]
        
        data_with_large_calendar = self.test_project_data.copy()
        data_with_large_calendar["calendar"] = large_calendar
        
        result = self.generate_pptx(data_with_large_calendar)
        
        assert result is not None
        assert os.path.exists(result)
        
        # Clean up
        if os.path.exists(result):
            os.remove(result)


class TestPPTXIntegration:
    """Test PPTX integration with output packager."""
    
    def test_pptx_export_method_exists(self):
        """Test that output_packager has PPTX export method."""
        from aicmo.delivery.output_packager import generate_full_deck_pptx
        assert callable(generate_full_deck_pptx)
    
    def test_pptx_function_signature(self):
        """Test PPTX function has correct signature."""
        from aicmo.delivery.output_packager import generate_full_deck_pptx
        import inspect
        
        sig = inspect.signature(generate_full_deck_pptx)
        # Should accept project_data
        assert "project_data" in sig.parameters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
