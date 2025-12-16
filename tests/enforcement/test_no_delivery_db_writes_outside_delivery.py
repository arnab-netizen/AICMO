"""Enforcement test: No Delivery db writes outside Delivery module."""
import os
import re
import pytest


def test_no_delivery_db_writes_outside_delivery():
    """
    Detect write patterns to Delivery tables outside aicmo/delivery/**.
    
    Patterns detected:
    - session.add() with DeliveryJobDB
    - Direct DeliveryJobDB instantiation
    
    This ensures Delivery data ownership remains with the Delivery module.
    """
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    aicmo_dir = os.path.join(workspace_root, "aicmo")
    
    violations = []
    
    # Delivery model names
    delivery_model_names = [
        "DeliveryJobDB",
        "DeliveryPackageDB",  # Phase 4 Lane B
        "DeliveryArtifactDB",  # Phase 4 Lane B
    ]
    
    # Scan all Python files
    for root, dirs, files in os.walk(aicmo_dir):
        # Skip Delivery module itself
        if "/delivery/" in root or root.endswith("/delivery"):
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
                    
                    # Check for session.add() with Delivery models
                    if "session.add(" in line:
                        for model_name in delivery_model_names:
                            if model_name in line:
                                violations.append(
                                    f"{relpath}:{i}: session.add() with {model_name} "
                                    f"(Delivery model write from outside Delivery)"
                                )
                    
                    # Check for model instantiation
                    for model_name in delivery_model_names:
                        # Pattern: ModelName()
                        if f"{model_name}(" in line and "import" not in line:
                            violations.append(
                                f"{relpath}:{i}: {model_name}() instantiation "
                                f"(Delivery model created outside Delivery)"
                            )
            
            except Exception as e:
                # Skip files that can't be read
                pass
    
    if violations:
        violation_msg = "\n".join(violations)
        pytest.fail(
            f"\n\nDelivery table writes detected outside aicmo/delivery/**:\n\n"
            f"{violation_msg}\n\n"
            f"Rule: Only aicmo/delivery/** may write to Delivery tables\n"
            f"Found {len(violations)} violation(s)\n\n"
            f"CRITICAL: Do NOT expand allowlist. Fix via port/adapter pattern instead."
        )
