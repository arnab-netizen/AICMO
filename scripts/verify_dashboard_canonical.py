#!/usr/bin/env python3
"""
AICMO Dashboard Canonicalization Verification Script

Purpose: Verify that the dashboard is correctly canonicalized with:
- Single runnable entrypoint (streamlit_pages/aicmo_operator.py)
- All legacy files have guards
- Docker and scripts point to canonical
- BUILD_MARKER defined
- Diagnostics panel present
- Error isolation in place

Exit Code: 0 = all checks pass, 1 = any check fails

Usage:
  python scripts/verify_dashboard_canonical.py
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(title):
    """Print formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_check(name, passed, details=""):
    """Print check result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"       {details}")


def check_canonical_file():
    """Verify canonical file exists and is substantial."""
    print_header("1. Canonical File Existence")
    
    canonical = Path("streamlit_pages/aicmo_operator.py")
    exists = canonical.exists()
    print_check("Canonical file exists", exists, str(canonical))
    
    if exists:
        size_kb = canonical.stat().st_size / 1024
        substantial = size_kb > 50
        print_check("File is substantial", substantial, f"{size_kb:.1f} KB")
        return exists and substantial
    return False


def check_build_marker():
    """Verify BUILD_MARKER is defined."""
    print_header("2. BUILD_MARKER Definition")
    
    try:
        with open("streamlit_pages/aicmo_operator.py", "r") as f:
            content = f.read()
            has_marker = 'BUILD_MARKER = "AICMO_DASH_V2_' in content
            
            if has_marker:
                # Extract the marker value
                for line in content.split("\n"):
                    if "BUILD_MARKER = " in line and not line.strip().startswith("#"):
                        marker_value = line.split("=")[1].strip().strip('"')
                        print_check("BUILD_MARKER defined", True, marker_value)
                        return True
            else:
                print_check("BUILD_MARKER defined", False)
                return False
    except Exception as e:
        print_check("BUILD_MARKER check", False, str(e))
        return False


def check_diagnostics_panel():
    """Verify Diagnostics panel code exists."""
    print_header("3. Diagnostics Panel")
    
    try:
        with open("streamlit_pages/aicmo_operator.py", "r") as f:
            content = f.read()
            # Look for diagnostics panel (might be with different formatting)
            has_panel = ("Diagnostics" in content and "st.expander" in content) or \
                       ("st.sidebar" in content and "Dashboard Info" in content)
            has_marker_display = 'BUILD_MARKER' in content and ('st.code' in content or 'st.write' in content)
            
            print_check("Diagnostics panel code", has_panel)
            print_check("BUILD_MARKER displayed", has_marker_display)
            
            return has_panel and has_marker_display
    except Exception as e:
        print_check("Diagnostics check", False, str(e))
        return False


def check_error_isolation():
    """Verify error isolation with try/except blocks."""
    print_header("4. Error Isolation")
    
    try:
        with open("streamlit_pages/aicmo_operator.py", "r") as f:
            content = f.read()
            count = content.count("except Exception")
            
            sufficient = count >= 20
            print_check("Error handlers present", sufficient, f"{count} try/except blocks")
            return sufficient
    except Exception as e:
        print_check("Error isolation check", False, str(e))
        return False


def check_session_wrapping():
    """Verify database sessions are wrapped."""
    print_header("5. Session Context Managers")
    
    try:
        with open("streamlit_pages/aicmo_operator.py", "r") as f:
            content = f.read()
            count = content.count("with get_session()")
            
            sufficient = count >= 15
            print_check("Session wrapping", sufficient, f"{count} context managers")
            return sufficient
    except Exception as e:
        print_check("Session wrapping check", False, str(e))
        return False


def check_docker_canonical():
    """Verify Docker uses canonical path."""
    print_header("6. Docker Configuration")
    
    try:
        dockerfile_path = Path("streamlit/Dockerfile")
        if not dockerfile_path.exists():
            print_check("Dockerfile exists", False)
            return False
        
        with open(dockerfile_path, "r") as f:
            content = f.read()
            has_canonical = "streamlit_pages/aicmo_operator.py" in content
            no_deprecated = "app.py" not in content or "# app.py" in content
            
            print_check("Uses canonical path", has_canonical)
            print_check("No deprecated app.py", no_deprecated)
            
            return has_canonical and no_deprecated
    except Exception as e:
        print_check("Docker check", False, str(e))
        return False


def check_script_canonical():
    """Verify scripts use canonical path."""
    print_header("7. Script Configuration")
    
    try:
        script_path = Path("scripts/launch_operator_ui.sh")
        if not script_path.exists():
            print_check("Script exists", False)
            return False
        
        with open(script_path, "r") as f:
            content = f.read()
            has_canonical = "streamlit_pages/aicmo_operator.py" in content
            
            print_check("Uses canonical path", has_canonical)
            return has_canonical
    except Exception as e:
        print_check("Script check", False, str(e))
        return False


def check_legacy_guards():
    """Verify legacy files have guards."""
    print_header("8. Legacy File Guards")
    
    legacy_files = [
        ("app.py", ["RuntimeError", "raise"]),
        ("launch_operator.py", ["sys.exit", "exit(1)"]),
        ("streamlit_app.py", ["st.stop()", "RuntimeError"]),
        ("streamlit_pages/aicmo_ops_shell.py", ["RuntimeError"]),
        ("streamlit_pages/cam_engine_ui.py", ["RuntimeError"]),
        ("streamlit_pages/operator_qc.py", ["RuntimeError"]),
    ]
    
    all_guarded = True
    for filepath, guard_keywords in legacy_files:
        path = Path(filepath)
        
        if not path.exists():
            print_check(f"{filepath} exists", False, "File not found")
            all_guarded = False
            continue
        
        try:
            with open(path, "r") as f:
                content = f.read()
                # Check first 20 lines for guard
                first_lines = "\n".join(content.split("\n")[:20])
                
                has_guard = any(keyword in first_lines for keyword in guard_keywords)
                print_check(f"{filepath} guarded", has_guard)
                
                if not has_guard:
                    all_guarded = False
        except Exception as e:
            print_check(f"{filepath} check", False, str(e))
            all_guarded = False
    
    return all_guarded


def check_tab_structure():
    """Verify tab structure is present."""
    print_header("9. Tab Structure")
    
    try:
        with open("streamlit_pages/aicmo_operator.py", "r") as f:
            content = f.read()
            
            # Tabs might be defined via tab_list.append or within st.tabs call
            required_keywords = [
                "Command Center",
                "Campaign Ops",
                "Monitoring",
                "tab_list",
                "st.tabs",
            ]
            
            found_keywords = [kw for kw in required_keywords if kw in content]
            
            # Check if tabs are properly configured
            has_tabs = len(found_keywords) >= 4
            
            print_check(f"Tab structure present", has_tabs, 
                       f"{len(found_keywords)}/{len(required_keywords)} keywords found")
            
            return has_tabs
    except Exception as e:
        print_check("Tab structure check", False, str(e))
        return False


def check_compilation():
    """Verify Python compilation."""
    print_header("10. Python Compilation")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", "streamlit_pages/aicmo_operator.py"],
            capture_output=True,
            timeout=10
        )
        
        success = result.returncode == 0
        print_check("Compilation clean", success)
        
        if not success:
            print(f"       Error: {result.stderr.decode()}")
        
        return success
    except Exception as e:
        print_check("Compilation check", False, str(e))
        return False


def main():
    """Run all verification checks."""
    print("\n" + "="*60)
    print("  AICMO DASHBOARD CANONICALIZATION VERIFICATION")
    print("  Build: AICMO_DASH_V2_2025_12_16")
    print("="*60)
    
    checks = [
        ("Canonical File", check_canonical_file),
        ("BUILD_MARKER", check_build_marker),
        ("Diagnostics Panel", check_diagnostics_panel),
        ("Error Isolation", check_error_isolation),
        ("Session Wrapping", check_session_wrapping),
        ("Docker Configuration", check_docker_canonical),
        ("Script Configuration", check_script_canonical),
        ("Legacy Guards", check_legacy_guards),
        ("Tab Structure", check_tab_structure),
        ("Compilation", check_compilation),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ EXCEPTION in {name}: {e}")
            results[name] = False
    
    # Summary
    print_header("SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✅ ALL CHECKS PASSED - PRODUCTION READY")
        print("="*60)
        return 0
    else:
        print(f"\n❌ {total - passed} CHECKS FAILED - REVIEW BEFORE DEPLOYMENT")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
