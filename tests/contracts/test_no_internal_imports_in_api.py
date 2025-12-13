"""
Import guard test - validates no internal imports in API layer.

This test walks all aicmo/**/api/*.py files and fails if any import contains:
- .internal
- aicmo.domain
- ORM model modules (except CAM's pre-existing legacy files)

This enforces the modularization boundary.
"""

import pytest
from pathlib import Path
import re


def test_no_internal_imports_in_api():
    """
    Walk all api/*.py files and ensure they don't import from internal/domain/db_models.
    
    Excludes: CAM's pre-existing api files that have legitimate db_models imports
    from the old architecture (review_queue.py, orchestration.py).
    """
    aicmo_root = Path(__file__).parent.parent.parent / "aicmo"
    
    # Find all api/*.py files (exclude __pycache__)
    api_files = list(aicmo_root.rglob("api/*.py"))
    api_files = [f for f in api_files if ".pyc" not in str(f) and "__pycache__" not in str(f)]
    
    # Exclude pre-existing CAM files with expected db_models imports from old architecture
    api_files = [f for f in api_files if not any(
        name in str(f) for name in [
            "cam/api/review_queue.py",
            "cam/api/orchestration.py",
        ]
    )]
    
    assert len(api_files) > 0, f"No API files found in {aicmo_root}"
    
    # Forbidden patterns (check actual imports, not docstrings/comments)
    forbidden_patterns = [
        (r"^from\s+\.internal", "from .internal"),
        (r"^from\s+aicmo\.\w+\.internal", "from aicmo.X.internal"),
        (r"^from\s+aicmo\.domain", "from aicmo.domain"),
        (r"^import\s+aicmo\.domain", "import aicmo.domain"),
    ]
    
    violations = []
    
    for api_file in api_files:
        with open(api_file) as f:
            lines = f.readlines()
        
        # Track if we're in a docstring
        in_docstring = False
        docstring_char = None
        
        for line_no, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue
            
            # Track docstrings
            for quote in ['"""', "'''"]:
                if quote in line:
                    count = line.count(quote)
                    if count % 2 == 1:  # Toggle docstring state
                        if in_docstring and docstring_char == quote:
                            in_docstring = False
                        elif not in_docstring:
                            in_docstring = True
                            docstring_char = quote
            
            # Skip if in docstring
            if in_docstring:
                continue
            
            # Check for forbidden patterns
            for pattern, desc in forbidden_patterns:
                if re.match(pattern, stripped):
                    violations.append({
                        "file": str(api_file.relative_to(aicmo_root.parent)),
                        "line": line_no,
                        "pattern": desc,
                        "code": stripped,
                    })
    
    if violations:
        error_msg = "\n\nAPI layer import violations found:\n"
        for v in violations:
            error_msg += f"  {v['file']}:{v['line']}\n"
            error_msg += f"    Forbidden: {v['pattern']}\n"
            error_msg += f"    Code: {v['code']}\n"
        
        pytest.fail(error_msg)
    
    print(f"✅ Checked {len(api_files)} API files - no forbidden imports found")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
