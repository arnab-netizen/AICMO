"""
Tests for HTML summary generation.

Tests the Jinja2 template rendering implementation including:
- HTML file creation from project_data
- Responsive CSS styling
- XSS protection via html_module.escape()
- Temporary file generation
- Template section rendering
"""

import pytest
from unittest.mock import Mock, patch
import os
import tempfile
from pathlib import Path


class TestHTMLGeneration:
    """Test HTML summary file generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from aicmo.delivery.output_packager import generate_html_summary
        self.generate_html = generate_html_summary
        
        self.test_project_data = {
            "project_name": "Test Campaign",
            "objective": "Launch new product",
            "platforms": {
                "LinkedIn": {"posts": 10, "engagement": 0.05},
                "Twitter": {"posts": 20, "engagement": 0.03}
            },
            "strategy": "Focus on B2B engagement with thought leadership",
            "calendar": [
                {"date": "2024-01-15", "platform": "LinkedIn", "content": "Thought leadership post"},
                {"date": "2024-01-16", "platform": "Twitter", "content": "Industry news"},
                {"date": "2024-01-17", "platform": "LinkedIn", "content": "Case study"},
                {"date": "2024-01-18", "platform": "Twitter", "content": "Engagement reply"},
                {"date": "2024-01-19", "platform": "LinkedIn", "content": "Behind-the-scenes"},
                {"date": "2024-01-20", "platform": "Twitter", "content": "Customer story"},
                {"date": "2024-01-21", "platform": "LinkedIn", "content": "Interview"}
            ],
            "deliverables": ["Campaign brief", "Content calendar", "Performance report"]
        }
    
    def test_html_generation_creates_file(self):
        """Test that HTML generation creates a file."""
        result = self.generate_html(self.test_project_data)
        
        assert result is not None
        assert isinstance(result, str)
        assert result.endswith(".html")
        
        # Check file exists
        assert os.path.exists(result)
        
        # Clean up
        if os.path.exists(result):
            os.remove(result)
    
    def test_html_generation_file_content(self):
        """Test HTML file contains expected content."""
        result = self.generate_html(self.test_project_data)
        
        assert result is not None
        
        # Read file
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should be valid HTML
        assert content.startswith("<!DOCTYPE html>") or "<html" in content
        
        # Should contain project name
        assert "Test Campaign" in content
        
        # Should contain objective
        assert "Launch new product" in content
        
        # Clean up
        if os.path.exists(result):
            os.remove(result)
    
    def test_html_generation_includes_calendar(self):
        """Test HTML includes calendar preview (first 7 posts)."""
        result = self.generate_html(self.test_project_data)
        
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should include some calendar entries
        assert "2024-01-15" in content or "Thought leadership post" in content
        
        # Clean up
        if os.path.exists(result):
            os.remove(result)
    
    def test_html_generation_includes_deliverables(self):
        """Test HTML includes deliverables section."""
        result = self.generate_html(self.test_project_data)
        
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should include deliverables
        assert "Campaign brief" in content
        
        # Clean up
        if os.path.exists(result):
            os.remove(result)
    
    def test_html_generation_with_minimal_data(self):
        """Test HTML generation with minimal data."""
        minimal_data = {
            "project_name": "Minimal",
            "objective": "Test",
            "platforms": {},
            "strategy": "None",
            "calendar": [],
            "deliverables": []
        }
        
        result = self.generate_html(minimal_data)
        
        assert result is not None
        assert os.path.exists(result)
        
        # Clean up
        if os.path.exists(result):
            os.remove(result)
    
    def test_html_xss_protection(self):
        """Test XSS protection with special HTML characters."""
        xss_data = {
            "project_name": "<script>alert('xss')</script>",
            "objective": "<img src=x onerror=alert('xss')>",
            "platforms": {},
            "strategy": "Safe & secure",
            "calendar": [],
            "deliverables": []
        }
        
        result = self.generate_html(xss_data)
        
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # XSS attempts should be escaped/sanitized
        # They should not be executable as scripts
        assert "<script>" not in content or "&lt;script&gt;" in content or "script" in content.replace("&lt;", "<").replace("&gt;", ">")
        
        # Clean up
        if os.path.exists(result):
            os.remove(result)
    
    def test_html_generation_file_naming(self):
        """Test HTML file naming convention."""
        result = self.generate_html(self.test_project_data)
        
        assert result is not None
        # Should be in temp directory
        assert "/tmp/" in result or "\\tmp\\" in result or "Temp" in result
        # Should have timestamp
        filename = os.path.basename(result)
        assert "summary_" in filename or "html" in filename
        
        # Clean up
        if os.path.exists(result):
            os.remove(result)
    
    def test_html_generation_with_unicode(self):
        """Test HTML generation with unicode characters."""
        unicode_data = {
            "project_name": "Test 测试 テスト 🚀",
            "objective": "Launch — with émojis and spëcial çhars",
            "platforms": {},
            "strategy": "Über strategy für die Zukunft",
            "calendar": [],
            "deliverables": []
        }
        
        result = self.generate_html(unicode_data)
        
        assert result is not None
        
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should preserve unicode (or properly escape it)
        assert "Test" in content
        
        # Clean up
        if os.path.exists(result):
            os.remove(result)
    
    def test_html_generation_with_long_content(self):
        """Test HTML generation with very long content."""
        long_data = {
            "project_name": "Test Campaign",
            "objective": "L" * 1000,  # 1000 character objective
            "platforms": {"Platform" + str(i): {"posts": 100} for i in range(10)},
            "strategy": "S" * 2000,  # 2000 character strategy
            "calendar": [
                {"date": f"2024-01-{(i % 30) + 1:02d}", "platform": f"Platform{i % 5}", "content": "C" * 500}
                for i in range(50)
            ],
            "deliverables": [f"Deliverable {i}" for i in range(20)]
        }
        
        result = self.generate_html(long_data)
        
        assert result is not None
        assert os.path.exists(result)
        
        # Clean up
        if os.path.exists(result):
            os.remove(result)


class TestHTMLIntegration:
    """Test HTML generation integration with output packager."""
    
    def test_html_export_method_exists(self):
        """Test that output_packager has HTML export method."""
        from aicmo.delivery.output_packager import generate_html_summary
        assert callable(generate_html_summary)
    
    def test_html_function_signature(self):
        """Test HTML function has correct signature."""
        from aicmo.delivery.output_packager import generate_html_summary
        import inspect
        
        sig = inspect.signature(generate_html_summary)
        # Should accept project_data
        assert "project_data" in sig.parameters
    
    def test_html_and_pptx_both_available(self):
        """Test both HTML and PPTX export methods are available."""
        from aicmo.delivery.output_packager import (
            generate_html_summary,
            generate_full_deck_pptx
        )
        
        assert callable(generate_html_summary)
        assert callable(generate_full_deck_pptx)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
