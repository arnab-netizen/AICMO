#!/usr/bin/env python3
"""
PHASE 7: Dashboard Import Smoke Test

Validates that all dashboard files and their dependencies can be imported
without errors. Does NOT run Streamlit UI; only checks Python syntax and
import chain.

Usage:
  python scripts/dashboard_import_smoke.py

Exit codes:
  0 - All imports successful
  1 - One or more imports failed
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

def test_import(module_path: str, description: str, expect_fail: bool = False) -> bool:
    """Try to import a module and report result.
    
    Args:
        module_path: Module path to import
        description: Human-readable description
        expect_fail: If True, expects import to fail (for guarded deprecated code)
    """
    try:
        parts = module_path.split('.')
        if len(parts) > 1:
            # Import as module
            __import__(module_path)
        else:
            # Load as file
            import importlib.util
            spec = importlib.util.spec_from_file_location(module_path, module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
        
        # If we expected a failure but didn't get one, that's bad
        if expect_fail:
            print(f"⚠️  {description} (expected to fail but didn't)")
            return False
        
        print(f"✅ {description}")
        return True
    except RuntimeError as e:
        if expect_fail and "DEPRECATED" in str(e):
            print(f"✅ {description} (correctly guarded)")
            return True
        print(f"❌ {description}: {type(e).__name__}: {str(e)[:100]}")
        return False
    except Exception as e:
        if expect_fail:
            print(f"✅ {description} (correctly blocked)")
            return True
        print(f"❌ {description}: {type(e).__name__}: {str(e)[:100]}")
        return False

def main():
    print("=" * 70)
    print("DASHBOARD IMPORT SMOKE TEST")
    print("=" * 70)
    print()
    
    results = []
    
    # Test canonical dashboard
    print("CANONICAL DASHBOARDS:")
    print("-" * 70)
    results.append(test_import(
        "streamlit_pages.aicmo_operator",
        "aicmo_operator.py (canonical UI)"
    ))
    print()
    
    # Test deprecated dashboards
    print("DEPRECATED DASHBOARDS (should guard and fail early):")
    print("-" * 70)
    results.append(test_import(
        "streamlit_pages.aicmo_ops_shell",
        "aicmo_ops_shell.py (should raise RuntimeError)",
        expect_fail=True
    ))
    results.append(test_import(
        "streamlit_pages.cam_engine_ui",
        "cam_engine_ui.py (should raise RuntimeError)",
        expect_fail=True
    ))
    results.append(test_import(
        "streamlit_pages.operator_qc",
        "operator_qc.py (should raise RuntimeError)",
        expect_fail=True
    ))
    print()
    
    # Test key dependencies
    print("CRITICAL DEPENDENCIES:")
    print("-" * 70)
    results.append(test_import(
        "aicmo.operator_services",
        "operator_services.py"
    ))
    results.append(test_import(
        "aicmo.core.db",
        "core/db.py"
    ))
    results.append(test_import(
        "aicmo.operator.dashboard_models",
        "operator/dashboard_models.py"
    ))
    results.append(test_import(
        "aicmo.operator.dashboard_service",
        "operator/dashboard_service.py"
    ))
    print()
    
    # Test optional dependencies
    print("OPTIONAL DEPENDENCIES:")
    print("-" * 70)
    try:
        import aicmo.campaign_ops
        print(f"✅ campaign_ops (available)")
        results.append(True)
    except ImportError as e:
        print(f"ℹ️  campaign_ops (not installed - this is OK if feature is disabled)")
        results.append(True)  # Don't fail on optional
    
    print()
    print("=" * 70)
    if all(results):
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        return 0
    else:
        failed = sum(1 for r in results if not r)
        print(f"❌ {failed} TEST(S) FAILED")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
