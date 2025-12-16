"""
Enforcement Test: No cross-module internal imports.

This test ensures that modules only import from other modules' public API,
never from their internal implementation.
"""
import os
import re
import pytest


def test_no_cross_module_internal_imports_runtime_scan():
    """
    Fail if any module imports another module's internal package.
    
    Rule: from aicmo.<module_x>.internal is only allowed within <module_x> itself.
    
    Example violations:
    - aicmo/strategy/internal/adapters.py importing from aicmo.production.internal
    - aicmo/delivery/orchestrator.py importing from aicmo.qc.internal
    
    Allowed:
    - aicmo/strategy/internal/adapters.py importing from aicmo.strategy.internal
    - aicmo/delivery/orchestrator.py importing from aicmo.qc.api
    """
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    aicmo_dir = os.path.join(workspace_root, "aicmo")
    
    violations = []
    
    # Known modules (from Phase 1)
    modules = [
        "billing", "cam", "client_review", "delivery", "identity",
        "learning", "observability", "onboarding", "orchestration",
        "production", "qc", "reporting", "retention", "strategy"
    ]
    
    # Scan all Python files
    for root, dirs, files in os.walk(aicmo_dir):
        # Determine which module this file belongs to
        # Extract from path like: /workspaces/AICMO/aicmo/strategy/internal/adapters.py
        rel_to_aicmo = os.path.relpath(root, aicmo_dir)
        path_parts = rel_to_aicmo.split(os.sep)
        
        if path_parts[0] == ".":
            # Root aicmo directory files (shared, etc.)
            current_module = None
        elif path_parts[0] in modules:
            current_module = path_parts[0]
        else:
            current_module = None
        
        for file in files:
            if not file.endswith(".py"):
                continue
            
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, workspace_root)
            
            # Skip __pycache__
            if "__pycache__" in filepath:
                continue
            
            # Allow composition root to wire dependencies from internal packages
            # This is the ONE place where cross-module internal imports are acceptable
            if "orchestration/composition/" in relpath:
                continue
            
            # Allow test files to import internals for testing purposes
            if relpath.startswith("tests/"):
                continue
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines, 1):
                    # Skip comments and docstrings
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    if stripped.startswith('"""') or stripped.startswith("'''"):
                        continue
                    
                    # Look for internal imports
                    # Pattern: from aicmo.<module>.internal
                    match = re.search(r'from\s+aicmo\.(\w+)\.internal', line)
                    if match:
                        imported_module = match.group(1)
                        
                        # Check if this is a cross-module import
                        if imported_module != current_module:
                            violations.append(
                                f"{relpath}:{i}: "
                                f"Cross-module internal import: "
                                f"from aicmo.{imported_module}.internal "
                                f"(current module: {current_module or 'N/A'})"
                            )
                    
                    # Also check: import aicmo.<module>.internal
                    match = re.search(r'import\s+aicmo\.(\w+)\.internal', line)
                    if match:
                        imported_module = match.group(1)
                        
                        if imported_module != current_module:
                            violations.append(
                                f"{relpath}:{i}: "
                                f"Cross-module internal import: "
                                f"import aicmo.{imported_module}.internal "
                                f"(current module: {current_module or 'N/A'})"
                            )
            
            except Exception as e:
                # Skip files that can't be read
                pass
    
    if violations:
        violation_msg = "\n".join(violations)
        pytest.fail(
            f"\n\nCross-module internal imports detected:\n\n"
            f"{violation_msg}\n\n"
            f"Rule: Modules may only import from other modules' public API (aicmo.<module>.api)\n"
            f"Found {len(violations)} violation(s)"
        )
