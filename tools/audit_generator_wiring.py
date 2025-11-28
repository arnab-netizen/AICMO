#!/usr/bin/env python3
"""
Audit script: Generator wiring, presets, WOW rules, and test coverage.
Produces detailed mapping of what's implemented vs. declared.
"""

import sys
import re
from pathlib import Path

# Add workspace root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))


def get_generators_from_backend():
    """Extract all SECTION_GENERATORS entries from backend/main.py"""
    main_py = repo_root / "backend" / "main.py"
    generators = set()

    with open(main_py, "r") as f:
        content = f.read()

    # Find SECTION_GENERATORS dict
    match = re.search(
        r"SECTION_GENERATORS:\s*dict\[str,\s*callable\]\s*=\s*\{(.*?)\n\}", content, re.DOTALL
    )
    if match:
        dict_content = match.group(1)
        # Extract all keys
        for line in dict_content.split("\n"):
            line = line.strip()
            if line.startswith('"') or line.startswith("'"):
                key_match = re.match(r'["\']([^"\']+)["\']', line)
                if key_match:
                    generators.add(key_match.group(1))

    return generators


def get_sections_from_presets():
    """Extract all sections declared in PACKAGE_PRESETS"""
    presets_py = repo_root / "aicmo" / "presets" / "package_presets.py"
    sections = set()

    with open(presets_py, "r") as f:
        content = f.read()

    # Find all "sections": [...] declarations
    for match in re.finditer(r'"sections"\s*:\s*\[(.*?)\]', content, re.DOTALL):
        section_list = match.group(1)
        for sec_match in re.finditer(r'["\']([^"\']+)["\']', section_list):
            sections.add(sec_match.group(1))

    return sections


def get_sections_from_wow_rules():
    """Extract all sections declared in WOW_RULES"""
    wow_py = repo_root / "aicmo" / "presets" / "wow_rules.py"
    sections = set()

    with open(wow_py, "r") as f:
        content = f.read()

    # Find all {"key": "..."} entries
    for match in re.finditer(r'\{"key"\s*:\s*"([^"]+)"\}', content):
        sections.add(match.group(1))

    return sections


def get_generator_functions_defined():
    """Find all _gen_* function definitions in backend/main.py"""
    main_py = repo_root / "backend" / "main.py"
    functions = set()

    with open(main_py, "r") as f:
        content = f.read()

    # Find all def _gen_* lines
    for match in re.finditer(r"def\s+(_gen_\w+)\s*\(", content):
        functions.add(match.group(1))

    return functions


def get_tests_for_functions():
    """Scan test files for function calls"""
    test_dir = repo_root / "tests"
    backend_test_dir = repo_root / "backend" / "tests"

    calls = {}

    for test_file in list(test_dir.glob("test_*.py")) + list(backend_test_dir.glob("test_*.py")):
        with open(test_file, "r") as f:
            content = f.read()

        # Count mentions of key functions
        for match in re.finditer(
            r"\b(_gen_\w+|SECTION_GENERATORS|validate_output|humanize_report)\b", content
        ):
            func = match.group(1)
            if func not in calls:
                calls[func] = []
            calls[func].append(str(test_file.relative_to(repo_root)))

    return calls


def main():
    print("=" * 80)
    print("AICMO GENERATOR WIRING AUDIT")
    print("=" * 80)

    generators = get_generators_from_backend()
    preset_sections = get_sections_from_presets()
    wow_sections = get_sections_from_wow_rules()
    defined_functions = get_generator_functions_defined()
    test_calls = get_tests_for_functions()

    print("\n📊 COUNTS:")
    print(f"  Generators registered: {len(generators)}")
    print(f"  Sections in presets: {len(preset_sections)}")
    print(f"  Sections in WOW rules: {len(wow_sections)}")
    print(f"  _gen_* functions defined: {len(defined_functions)}")
    print(f"  Unique declared sections: {len(preset_sections | wow_sections)}")

    # Find mismatches
    missing_generators = (preset_sections | wow_sections) - generators
    unused_generators = generators - (preset_sections | wow_sections)

    print(f"\n🔴 MISSING GENERATORS: {len(missing_generators)}")
    if missing_generators:
        for sec in sorted(missing_generators):
            in_preset = "✓ PRESET" if sec in preset_sections else ""
            in_wow = "✓ WOW" if sec in wow_sections else ""
            print(f"   - {sec:40} {in_preset} {in_wow}")

    print(f"\n🟡 UNUSED GENERATORS: {len(unused_generators)}")
    if unused_generators:
        for gen in sorted(unused_generators):
            print(f"   - {gen}")

    print(f"\n✅ FULLY IMPLEMENTED SECTIONS: {len(preset_sections & generators)}")

    print("\n🧪 TEST COVERAGE:")
    print(
        f"   Functions with tests: {len([x for x in defined_functions if any(x in call for call in test_calls.keys())])}"
    )

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
