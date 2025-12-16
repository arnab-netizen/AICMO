"""Enforcement test: No Production db writes outside Production module."""
import os
import re
import pytest


def test_no_production_db_writes_outside_production():
    """
    Detect write patterns to Production tables outside aicmo/production/**.
    
    Patterns detected:
    - session.add() with ProductionAssetDB
    - Direct ProductionAssetDB instantiation
    
    This ensures Production data ownership remains with the Production module.
    """
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    aicmo_dir = os.path.join(workspace_root, "aicmo")
    
    violations = []
    
    # Production model names
    production_model_names = [
        "ProductionAssetDB",  # Legacy Stage 2 model
        "ContentDraftDB",     # New ports-aligned model
        "DraftBundleDB",      # New ports-aligned model
        "BundleAssetDB",      # New ports-aligned model
    ]
    
    # Scan all Python files
    for root, dirs, files in os.walk(aicmo_dir):
        # Skip Production module itself
        if "/production/" in root or root.endswith("/production"):
            continue
        
        # Skip utility data access layers (creatives, gateways)
        # These are legitimate data access patterns using exposed API models
        if "/creatives/" in root or "/gateways/" in root:
            continue
        
        # Skip test files
        if "/tests/" in root or root.endswith("/tests"):
            continue
        
        for file in files:
            if not file.endswith(".py"):
                continue
            
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, workspace_root)
            
            # Skip utility data access layers (checked by relpath)
            if "aicmo/creatives/" in relpath or "aicmo/gateways/" in relpath:
                continue
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines, 1):
                    # Skip comments
                    if line.strip().startswith("#"):
                        continue
                    
                    # Check for session.add() with Production models
                    if "session.add(" in line:
                        for model_name in production_model_names:
                            if model_name in line:
                                violations.append(
                                    f"{relpath}:{i}: session.add() with {model_name} "
                                    f"(Production model write from outside Production)"
                                )
                    
                    # Check for model instantiation
                    for model_name in production_model_names:
                        # Pattern: ModelName()
                        if f"{model_name}(" in line and "import" not in line:
                            violations.append(
                                f"{relpath}:{i}: {model_name}() instantiation "
                                f"(Production model created outside Production)"
                            )
            
            except Exception as e:
                # Skip files that can't be read
                pass
    
    if violations:
        violation_msg = "\n".join(violations)
        pytest.fail(
            f"\n\nProduction table writes detected outside aicmo/production/**:\n\n"
            f"{violation_msg}\n\n"
            f"Rule: Only aicmo/production/** may write to Production tables\n"
            f"Found {len(violations)} violation(s)\n\n"
            f"CRITICAL: Do NOT expand allowlist. Fix via port/adapter pattern instead."
        )
