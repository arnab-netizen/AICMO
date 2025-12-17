#!/usr/bin/env python3
"""
AUDIT SCRIPT: Inventory environment variable usage.

Purpose:
  - Search for all os.getenv / os.environ patterns
  - Output ONLY env var names + file:line locations
  - DO NOT print actual values

Rules:
  - No secrets leaked
  - Safe to run in any environment
  - Machine-readable output for aggregation
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict

# Repository root
REPO_ROOT = Path(__file__).parent.parent
IGNORE_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache"}

def find_env_var_usages():
    """Search Python files for os.getenv / os.environ patterns."""
    
    results = defaultdict(list)  # {env_var_name: [(file, line_num), ...]}
    
    # Patterns to match:
    # 1. os.getenv("KEY") or os.getenv('KEY')
    # 2. os.environ["KEY"] or os.environ['KEY']
    # 3. os.environ.get("KEY") or os.environ.get('KEY')
    
    patterns = [
        r'os\.getenv\s*\(\s*["\']([A-Z_]+)["\']',
        r'os\.environ\s*\[\s*["\']([A-Z_]+)["\']',
        r'os\.environ\.get\s*\(\s*["\']([A-Z_]+)["\']',
    ]
    
    compiled_patterns = [re.compile(p) for p in patterns]
    
    # Walk repository
    for py_file in REPO_ROOT.rglob("*.py"):
        # Skip ignored dirs
        if any(ignore_dir in py_file.parts for ignore_dir in IGNORE_DIRS):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    for pattern in compiled_patterns:
                        matches = pattern.findall(line)
                        for env_var_name in matches:
                            # Only track if not already seen in this file
                            rel_path = py_file.relative_to(REPO_ROOT)
                            results[env_var_name].append((str(rel_path), line_num))
        except Exception as e:
            # Skip files that can't be read
            pass
    
    return results

def main():
    """Main audit runner."""
    
    print("=" * 80)
    print("AUDIT: Environment Variable Usage Inventory")
    print("=" * 80)
    print()
    
    results = find_env_var_usages()
    
    if not results:
        print("No environment variable usages found.")
        print()
        return
    
    # Sort by env var name
    sorted_vars = sorted(results.keys())
    
    print(f"Found {len(sorted_vars)} unique environment variables:\n")
    
    for env_var in sorted_vars:
        locations = results[env_var]
        print(f"\n{env_var}:")
        for file_path, line_num in sorted(set(locations)):
            print(f"  {file_path}:{line_num}")
    
    print()
    print("=" * 80)
    print(f"SUMMARY: {len(sorted_vars)} unique env vars across {sum(len(v) for v in results.values())} usages")
    print("=" * 80)

if __name__ == "__main__":
    main()
