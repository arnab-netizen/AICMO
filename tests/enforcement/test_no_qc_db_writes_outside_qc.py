"""Enforcement test: No QC db writes outside QC module."""
import os
import re
import pytest


def test_no_qc_db_writes_outside_qc():
    """
    Detect write patterns to QC tables outside aicmo/qc/**.
    
    Patterns detected:
    - session.add() with QcResultDB
    - session.add() with QcIssueDB
    - Direct QcResultDB/QcIssueDB instantiation
    
    This ensures QC data ownership remains with the QC module.
    """
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    aicmo_dir = os.path.join(workspace_root, "aicmo")
    
    violations = []
    
    # QC model names
    qc_model_names = [
        "QcResultDB",
        "QcIssueDB",
    ]
    
    # Scan all Python files
    for root, dirs, files in os.walk(aicmo_dir):
        # Skip QC module itself
        if "/qc/" in root or root.endswith("/qc"):
            continue
        
        # Skip test files
        if "/tests/" in root or root.endswith("/tests"):
            continue
        
        for file in files:
            if not file.endswith(".py"):
                continue
            
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, workspace_root)
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines, 1):
                    # Skip comments
                    if line.strip().startswith("#"):
                        continue
                    
                    # Check for session.add() with QC models
                    if "session.add(" in line:
                        for model_name in qc_model_names:
                            if model_name in line:
                                violations.append(
                                    f"{relpath}:{i}: session.add() with {model_name} "
                                    f"(QC model write from outside QC)"
                                )
                    
                    # Check for model instantiation
                    for model_name in qc_model_names:
                        # Pattern: ModelName()
                        if f"{model_name}(" in line and "import" not in line:
                            violations.append(
                                f"{relpath}:{i}: {model_name}() instantiation "
                                f"(QC model created outside QC)"
                            )
            
            except Exception as e:
                # Don't fail test on read errors, but log it
                print(f"Warning: Could not read {relpath}: {e}")
    
    # Fail if violations found
    if violations:
        msg = (
            "QC data ownership violation detected!\n"
            "Found QC DB writes outside aicmo/qc/internal/:\n\n"
            + "\n".join(violations)
            + "\n\nOnly aicmo/qc/internal/repositories_db.py should write to QC tables."
        )
        pytest.fail(msg)
