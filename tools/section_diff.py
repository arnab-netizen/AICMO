#!/usr/bin/env python3
"""
Compute authoritative diff between declared sections (presets + WOW) and registered generators.
Generates AICMO_SECTION_DIFF.md at repo root.
"""

import re
import sys
from pathlib import Path
from typing import Set, Dict

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


def extract_section_ids_from_presets() -> Set[str]:
    """Extract all section IDs from package_presets.py"""
    preset_file = REPO_ROOT / "aicmo" / "presets" / "package_presets.py"

    if not preset_file.exists():
        print(f"ERROR: {preset_file} not found")
        return set()

    content = preset_file.read_text()

    # Find all "sections": [...] blocks and extract the quoted strings within
    # Pattern: "sections": [ ... quoted strings ... ]
    sections_pattern = re.compile(r'"sections"\s*:\s*\[(.*?)\]', re.DOTALL)

    section_ids = set()
    for match in sections_pattern.finditer(content):
        block = match.group(1)
        # Extract all quoted strings from this block
        quoted_pattern = re.compile(r'["\']([a-z0-9_]+)["\']')
        for quoted_match in quoted_pattern.finditer(block):
            section_ids.add(quoted_match.group(1))

    return section_ids


def extract_section_ids_from_wow() -> Set[str]:
    """Extract all section IDs from wow_rules.py"""
    wow_file = REPO_ROOT / "aicmo" / "presets" / "wow_rules.py"

    if not wow_file.exists():
        print(f"ERROR: {wow_file} not found")
        return set()

    content = wow_file.read_text()

    # Find all "sections": [...] blocks and extract the quoted strings within
    sections_pattern = re.compile(r'"sections"\s*:\s*\[(.*?)\]', re.DOTALL)

    section_ids = set()
    for match in sections_pattern.finditer(content):
        block = match.group(1)
        # Extract all quoted strings from this block
        quoted_pattern = re.compile(r'["\']([a-z0-9_]+)["\']')
        for quoted_match in quoted_pattern.finditer(block):
            section_ids.add(quoted_match.group(1))

    return section_ids


def extract_registered_generators() -> Set[str]:
    """Extract all registered section IDs from backend/main.py SECTION_GENERATORS"""
    main_file = REPO_ROOT / "backend" / "main.py"

    if not main_file.exists():
        print(f"ERROR: {main_file} not found")
        return set()

    content = main_file.read_text()

    # Find SECTION_GENERATORS dict and extract all keys
    # Pattern: "section_id": _gen_function,
    section_pattern = re.compile(r'["\']([a-z0-9_]+)["\']:\s*_gen_')

    matches = section_pattern.findall(content)

    return set(matches)


def main():
    print("=" * 80)
    print("AICMO Section Diff Analysis")
    print("=" * 80)

    # Extract sections from all sources
    print("\nExtracting sections from presets...")
    preset_sections = extract_section_ids_from_presets()
    print(f"  Found {len(preset_sections)} unique section IDs")

    print("Extracting sections from WOW rules...")
    wow_sections = extract_section_ids_from_wow()
    print(f"  Found {len(wow_sections)} unique section IDs")

    print("Extracting registered generators...")
    registered_sections = extract_registered_generators()
    print(f"  Found {len(registered_sections)} registered generators")

    # Compute diffs
    all_declared = preset_sections | wow_sections
    missing_generators = all_declared - registered_sections
    unused_generators = registered_sections - all_declared

    print("\nAnalysis:")
    print(f"  Sections in presets: {len(preset_sections)}")
    print(f"  Sections in WOW rules: {len(wow_sections)}")
    print(f"  Unique declared sections: {len(all_declared)}")
    print(f"  Registered generators: {len(registered_sections)}")
    print(f"  Missing generators: {len(missing_generators)}")
    print(f"  Unused generators: {len(unused_generators)}")

    # Generate markdown report
    report_file = REPO_ROOT / "AICMO_SECTION_DIFF.md"

    with open(report_file, "w") as f:
        f.write("# AICMO Section Diff (Authoritative)\n\n")

        f.write("## Summary\n\n")
        f.write(f"- Sections in presets: {len(preset_sections)}\n")
        f.write(f"- Sections in WOW rules: {len(wow_sections)}\n")
        f.write(f"- Unique declared sections (presets ∪ WOW): {len(all_declared)}\n")
        f.write(f"- Registered generators: {len(registered_sections)}\n")
        f.write(f"- **Missing generators:** {len(missing_generators)}\n")
        f.write(f"- **Unused generators:** {len(unused_generators)}\n\n")

        if missing_generators:
            f.write("## Missing Generators\n\n")
            f.write(
                "These sections are declared in presets or WOW but have no corresponding generator:\n\n"
            )
            f.write("| section_id | in_presets | in_wow |\n")
            f.write("|-----------|-----------|--------|\n")
            for section_id in sorted(missing_generators):
                in_presets = "✓" if section_id in preset_sections else ""
                in_wow = "✓" if section_id in wow_sections else ""
                f.write(f"| `{section_id}` | {in_presets} | {in_wow} |\n")
            f.write("\n")
        else:
            f.write("## Missing Generators\n\nNone! ✅\n\n")

        if unused_generators:
            f.write("## Unused Generators\n\n")
            f.write("These generators are registered but not used in any preset or WOW rule:\n\n")
            f.write("| section_id |\n")
            f.write("|----------|\n")
            for section_id in sorted(unused_generators):
                f.write(f"| `{section_id}` |\n")
            f.write("\n")
        else:
            f.write("## Unused Generators\n\nNone! ✅\n\n")

        f.write("## Preset Section Distribution\n\n")
        f.write("| section_id | count |\n")
        f.write("|-----------|-------|\n")
        section_count: Dict[str, int] = {}
        for section in preset_sections:
            section_count[section] = section_count.get(section, 0) + 1
        for section_id in sorted(section_count.keys()):
            f.write(f"| `{section_id}` | {section_count[section_id]} |\n")
        f.write("\n")

        f.write("---\n")
        f.write("*Generated by tools/section_diff.py*\n")

    print(f"\n✅ Report generated: {report_file}")

    # Return exit code 0 if no missing generators, non-zero otherwise
    return 0 if len(missing_generators) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
