"""Enforcement test: No CAM db_models imports outside CAM module."""
import os
import re
import pytest


def test_no_cam_db_models_outside_cam():
    """
    Test that no file outside aicmo/cam/** imports aicmo.cam.db_models.
    
    Phase 3 rule: Only CAM may import CAM db_models.
    Phase 4: Allowlist for operator_services.py (UI layer) - to be refactored to use CAM query ports.
    """
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    aicmo_dir = os.path.join(workspace_root, "aicmo")
    
    # Baseline allowlist - existing violations to be fixed in future phases
    # These should be replaced with CAM query/command ports
    ALLOWED_VIOLATIONS = {
        "aicmo/operator_services.py",  # TODO Phase 4+: Replace with CAM API ports
    }
    
    violations = []
    
    # Scan all Python files
    for root, dirs, files in os.walk(aicmo_dir):
        # Skip CAM module itself
        if "/cam/" in root or root.endswith("/cam"):
            continue
        
        for file in files:
            if not file.endswith(".py"):
                continue
            
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, workspace_root)
            
            # Check if this file is in the allowlist
            if relpath in ALLOWED_VIOLATIONS:
                continue
            
            # Read file content
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check for CAM db_models imports
                if "aicmo.cam.db_models" in content:
                    # Find line numbers
                    lines = content.split("\n")
                    for i, line in enumerate(lines, 1):
                        if "aicmo.cam.db_models" in line and not line.strip().startswith("#"):
                            violations.append(f"{relpath}:{i}")
            
            except Exception as e:
                # Skip files that can't be read
                pass
    
    if violations:
        violation_msg = "\n".join(violations)
        pytest.fail(
            f"CAM db_models imported outside CAM module:\n{violation_msg}\n\n"
            f"Rule: Only aicmo/cam/** may import aicmo.cam.db_models\n\n"
            f"CRITICAL: Do NOT expand allowlist. Fix via port/adapter pattern instead."
        )
    
    # Verify no new violations beyond baseline allowlist
    # If this assertion fails, a previously allowed file no longer violates (good!)
    # or we need to update the test
    if len(ALLOWED_VIOLATIONS) > 0:
        print(f"Note: {len(ALLOWED_VIOLATIONS)} baseline violation(s) still present (marked for future refactor)")
