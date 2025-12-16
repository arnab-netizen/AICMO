"""
Enforcement Test: No CAM session writes outside CAM internal.

This test detects write operations to CAM tables from outside CAM internal.
Uses pattern matching to find session.add() calls with CAM models.
"""
import os
import re
import pytest


def test_no_cam_session_writes_outside_cam_internal():
    """
    Detect write patterns to CAM tables outside aicmo/cam/internal/**.
    
    Patterns detected:
    - session.add() with CAM model imports
    - Direct CAM model instantiation followed by session operations
    
    This is best-effort but strict: any suspicious pattern fails the test.
    
    Allowlist: cam/worker/** - infrastructure code that writes heartbeats/metadata
    """
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    aicmo_dir = os.path.join(workspace_root, "aicmo")
    
    violations = []
    
    # CAM model names to detect (known from audit)
    cam_model_names = [
        "CampaignDB",
        "LeadDB",
        "OutreachAttemptDB",
        "ContactEventDB",
        "DiscoveryJobDB",
        "SafetySettingsDB",
        "ChannelConfigDB",
        # CreativeAssetDB moved to Production module (ProductionAssetDB)
        # ExecutionJobDB moved to Delivery module (DeliveryJobDB)
        "OutboundEmailDB",
        "InboundEmailDB",
        "CamWorkerHeartbeatDB",
        "CronExecutionDB",
    ]
    
    # Scan all Python files
    for root, dirs, files in os.walk(aicmo_dir):
        # Skip CAM internal directory
        if "/cam/internal" in root or root.endswith("/cam/internal"):
            continue
        
        # Skip CAM worker directory (infrastructure code)
        if "/cam/worker" in root or root.endswith("/cam/worker"):
            continue
        
        for file in files:
            if not file.endswith(".py"):
                continue
            
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, workspace_root)
            
            # Skip __pycache__
            if "__pycache__" in filepath:
                continue
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")
                
                # Check if file imports CAM db_models
                imports_cam_models = "aicmo.cam.db_models" in content
                
                if not imports_cam_models:
                    continue  # No CAM imports, skip
                
                # Now look for write patterns
                for i, line in enumerate(lines, 1):
                    # Pattern 1: session.add() with CAM model variable
                    if "session.add(" in line:
                        # Check if any CAM model name appears in nearby context
                        # Look at surrounding lines (5 lines before)
                        start = max(0, i - 6)
                        context = "\n".join(lines[start:i])
                        
                        for model_name in cam_model_names:
                            if f"{model_name}()" in context or f"= {model_name}" in context:
                                violations.append(
                                    f"{relpath}:{i}: session.add() with {model_name} "
                                    f"(CAM model write from outside CAM)"
                                )
                                break
                    
                    # Pattern 2: Direct model instantiation
                    for model_name in cam_model_names:
                        if f"{model_name}()" in line and "from aicmo.cam.db_models" not in line:
                            # This line instantiates a CAM model
                            violations.append(
                                f"{relpath}:{i}: {model_name}() instantiation "
                                f"(CAM model created outside CAM)"
                            )
            
            except Exception as e:
                # Skip files that can't be read
                pass
    
    if violations:
        violation_msg = "\n".join(violations)
        pytest.fail(
            f"\n\nCAM table writes detected outside aicmo/cam/internal/**:\n\n"
            f"{violation_msg}\n\n"
            f"Rule: Only aicmo/cam/internal/** may write to CAM tables\n"
            f"Found {len(violations)} violation(s)\n\n"
            f"CRITICAL: Do NOT expand allowlist. Fix via port/adapter pattern instead."
        )
