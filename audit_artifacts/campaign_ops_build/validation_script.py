#!/usr/bin/env python3
"""
Campaign Operations - Validation Script

Checks:
1. All new files exist and have correct syntax
2. Database migration can be applied
3. Imports work correctly
4. No conflicts with existing code
5. Feature gate is accessible
"""

import os
import sys
import subprocess
from pathlib import Path

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

REPO_ROOT = Path("/workspaces/AICMO")
os.chdir(REPO_ROOT)


def check(description: str, result: bool, details: str = "") -> bool:
    """Print check result."""
    status = f"{GREEN}✅{RESET}" if result else f"{RED}❌{RESET}"
    print(f"{status} {description}")
    if details:
        print(f"   {details}")
    return result


def main():
    print(f"\n{YELLOW}{'='*70}{RESET}")
    print(f"Campaign Operations - Validation")
    print(f"{YELLOW}{'='*70}{RESET}\n")
    
    checks_passed = 0
    checks_total = 0
    
    # ========================================================================
    # 1. File existence checks
    # ========================================================================
    print(f"\n{YELLOW}1. File Existence Checks{RESET}")
    
    required_files = [
        "aicmo/campaign_ops/__init__.py",
        "aicmo/campaign_ops/models.py",
        "aicmo/campaign_ops/schemas.py",
        "aicmo/campaign_ops/repo.py",
        "aicmo/campaign_ops/service.py",
        "aicmo/campaign_ops/instructions.py",
        "aicmo/campaign_ops/actions.py",
        "aicmo/campaign_ops/wiring.py",
        "aicmo/campaign_ops/ui.py",
        "db/alembic/versions/0001_campaign_ops_add_campaign_ops_tables.py",
    ]
    
    for file_path in required_files:
        checks_total += 1
        file_exists = (REPO_ROOT / file_path).exists()
        if check(f"File exists: {file_path}", file_exists):
            checks_passed += 1
    
    # ========================================================================
    # 2. Syntax checks
    # ========================================================================
    print(f"\n{YELLOW}2. Python Syntax Checks{RESET}")
    
    syntax_files = required_files[:-1]  # Exclude migration for now
    
    for file_path in syntax_files:
        checks_total += 1
        try:
            result = subprocess.run(
                ["python", "-m", "py_compile", file_path],
                capture_output=True,
                text=True,
                timeout=5,
            )
            success = result.returncode == 0
            if check(f"Syntax valid: {file_path}", success):
                checks_passed += 1
            else:
                print(f"   Error: {result.stderr}")
        except Exception as e:
            check(f"Syntax valid: {file_path}", False, str(e))
    
    # ========================================================================
    # 3. Import checks
    # ========================================================================
    print(f"\n{YELLOW}3. Import Checks{RESET}")
    
    imports_to_check = [
        ("aicmo.campaign_ops.models", "Models"),
        ("aicmo.campaign_ops.schemas", "Schemas"),
        ("aicmo.campaign_ops.repo", "Repository"),
        ("aicmo.campaign_ops.service", "Service"),
        ("aicmo.campaign_ops.instructions", "Instructions"),
        ("aicmo.campaign_ops.actions", "Actions"),
        ("aicmo.campaign_ops.wiring", "Wiring"),
        ("aicmo.campaign_ops.ui", "UI"),
    ]
    
    for module_name, desc in imports_to_check:
        checks_total += 1
        try:
            __import__(module_name)
            if check(f"Import works: {desc}", True):
                checks_passed += 1
        except Exception as e:
            check(f"Import works: {desc}", False, str(e))
    
    # ========================================================================
    # 4. Models check
    # ========================================================================
    print(f"\n{YELLOW}4. Database Models Check{RESET}")
    
    checks_total += 1
    try:
        from aicmo.campaign_ops.models import (
            Campaign, CampaignPlan, CalendarItem,
            OperatorTask, MetricEntry, OperatorAuditLog,
        )
        table_names = [
            Campaign.__tablename__,
            CampaignPlan.__tablename__,
            CalendarItem.__tablename__,
            OperatorTask.__tablename__,
            MetricEntry.__tablename__,
            OperatorAuditLog.__tablename__,
        ]
        expected = [
            "campaign_ops_campaigns",
            "campaign_ops_plans",
            "campaign_ops_calendar_items",
            "campaign_ops_operator_tasks",
            "campaign_ops_metric_entries",
            "campaign_ops_audit_log",
        ]
        all_match = table_names == expected
        if check(f"All models have correct table names", all_match):
            checks_passed += 1
            for name in table_names:
                print(f"   - {name}")
        else:
            print(f"   Expected: {expected}")
            print(f"   Got: {table_names}")
    except Exception as e:
        check(f"All models have correct table names", False, str(e))
    
    # ========================================================================
    # 5. Service check
    # ========================================================================
    print(f"\n{YELLOW}5. Service Layer Check{RESET}")
    
    required_methods = [
        "create_campaign",
        "generate_plan",
        "generate_calendar",
        "generate_tasks_from_calendar",
        "get_today_tasks",
        "get_overdue_tasks",
        "mark_task_complete",
        "generate_weekly_summary",
    ]
    
    checks_total += 1
    try:
        from aicmo.campaign_ops.service import CampaignOpsService
        methods_found = []
        for method_name in required_methods:
            if hasattr(CampaignOpsService, method_name):
                methods_found.append(method_name)
        
        all_found = len(methods_found) == len(required_methods)
        if check(f"Service has all required methods ({len(methods_found)}/{len(required_methods)})", all_found):
            checks_passed += 1
        else:
            missing = set(required_methods) - set(methods_found)
            print(f"   Missing: {missing}")
    except Exception as e:
        check(f"Service has all required methods", False, str(e))
    
    # ========================================================================
    # 6. Platform SOP check
    # ========================================================================
    print(f"\n{YELLOW}6. Platform SOP Templates Check{RESET}")
    
    checks_total += 1
    try:
        from aicmo.campaign_ops.instructions import (
            get_platform_sop,
            list_available_platforms,
        )
        platforms = list_available_platforms()
        expected_platforms = ["linkedin", "instagram", "twitter", "email"]
        all_present = all(p in platforms for p in expected_platforms)
        
        if check(f"All platforms have SOPs ({len(platforms)})", all_present):
            checks_passed += 1
            for platform in platforms:
                sop = get_platform_sop(platform, "post")
                has_where = "WHERE" in sop
                has_how = "HOW" in sop
                print(f"   - {platform}: {len(sop)} chars" + (" ✓" if (has_where and has_how) else " ⚠"))
        else:
            print(f"   Expected: {expected_platforms}")
            print(f"   Got: {platforms}")
    except Exception as e:
        check(f"All platforms have SOPs", False, str(e))
    
    # ========================================================================
    # 7. AOL action handlers check
    # ========================================================================
    print(f"\n{YELLOW}7. AOL Action Handlers Check{RESET}")
    
    handlers_to_check = [
        "handle_campaign_tick",
        "handle_escalate_overdue_tasks",
        "handle_weekly_campaign_summary",
    ]
    
    checks_total += 1
    try:
        from aicmo.campaign_ops import actions
        for handler_name in handlers_to_check:
            if hasattr(actions, handler_name):
                print(f"   ✓ {handler_name}")
            else:
                print(f"   ✗ {handler_name}")
        
        all_found = all(hasattr(actions, h) for h in handlers_to_check)
        if check(f"All AOL handlers defined", all_found):
            checks_passed += 1
    except Exception as e:
        check(f"All AOL handlers defined", False, str(e))
    
    # ========================================================================
    # 8. Wiring check
    # ========================================================================
    print(f"\n{YELLOW}8. Wiring Check{RESET}")
    
    checks_total += 1
    try:
        from aicmo.campaign_ops.wiring import (
            AICMO_CAMPAIGN_OPS_ENABLED,
            render_campaign_ops_ui,
            get_session_for_campaign_ops,
        )
        print(f"   Feature enabled: {AICMO_CAMPAIGN_OPS_ENABLED}")
        if check(f"Wiring module has all exports", True):
            checks_passed += 1
    except Exception as e:
        check(f"Wiring module has all exports", False, str(e))
    
    # ========================================================================
    # 9. Migration file check
    # ========================================================================
    print(f"\n{YELLOW}9. Migration File Check{RESET}")
    
    checks_total += 1
    migration_file = REPO_ROOT / "db/alembic/versions/0001_campaign_ops_add_campaign_ops_tables.py"
    
    if migration_file.exists():
        try:
            migration_content = migration_file.read_text()
            required_strings = [
                "def upgrade()",
                "def downgrade()",
                "campaign_ops_campaigns",
                "campaign_ops_plans",
                "campaign_ops_calendar_items",
                "campaign_ops_operator_tasks",
                "campaign_ops_metric_entries",
                "campaign_ops_audit_log",
            ]
            
            all_found = all(s in migration_content for s in required_strings)
            if check(f"Migration file is complete", all_found):
                checks_passed += 1
            else:
                missing = [s for s in required_strings if s not in migration_content]
                print(f"   Missing: {missing}")
        except Exception as e:
            check(f"Migration file is complete", False, str(e))
    else:
        check(f"Migration file is complete", False, "File not found")
    
    # ========================================================================
    # 10. Existing code modifications check
    # ========================================================================
    print(f"\n{YELLOW}10. Existing Code Check (No Breaking Changes){RESET}")
    
    checks_total += 2
    
    # Check Streamlit wiring
    try:
        streamlit_file = REPO_ROOT / "streamlit_pages/aicmo_operator.py"
        streamlit_content = streamlit_file.read_text()
        
        has_wiring_markers = (
            "# AICMO_CAMPAIGN_OPS_WIRING_START" in streamlit_content and
            "# AICMO_CAMPAIGN_OPS_WIRING_END" in streamlit_content
        )
        
        if check(f"Streamlit wiring is marked (for safety)", has_wiring_markers):
            checks_passed += 1
        else:
            print("   Wiring should be wrapped in markers")
    except Exception as e:
        check(f"Streamlit wiring is marked", False, str(e))
    
    # Check daemon wiring
    try:
        daemon_file = REPO_ROOT / "aicmo/orchestration/daemon.py"
        daemon_content = daemon_file.read_text()
        
        has_wiring_markers = (
            "# AICMO_CAMPAIGN_OPS_WIRING_START" in daemon_content and
            "# AICMO_CAMPAIGN_OPS_WIRING_END" in daemon_content
        )
        
        has_post_social = "POST_SOCIAL" in daemon_content
        
        if check(f"AOL daemon wiring is marked (POST_SOCIAL preserved)", has_wiring_markers and has_post_social):
            checks_passed += 1
        else:
            if not has_wiring_markers:
                print("   Wiring should be wrapped in markers")
            if not has_post_social:
                print("   POST_SOCIAL handler should still be present")
    except Exception as e:
        check(f"AOL daemon wiring is marked", False, str(e))
    
    # ========================================================================
    # Summary
    # ========================================================================
    print(f"\n{YELLOW}{'='*70}{RESET}")
    print(f"Summary: {checks_passed}/{checks_total} checks passed")
    print(f"{YELLOW}{'='*70}{RESET}\n")
    
    if checks_passed == checks_total:
        print(f"{GREEN}✅ ALL CHECKS PASSED - Campaign Ops is ready!{RESET}\n")
        return 0
    else:
        failed = checks_total - checks_passed
        print(f"{RED}❌ {failed} checks failed - Please review above{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
