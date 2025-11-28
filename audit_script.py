#!/usr/bin/env python3
"""
AICMO Comprehensive Audit Script
Analyzes repository structure, wiring, and test coverage
"""

import ast
from pathlib import Path

# ============================================================================
# PART 1: REPO STRUCTURE MAPPING
# ============================================================================


def scan_directory_structure():
    """Map all key directories and modules."""
    root = Path("/workspaces/AICMO")

    structure = {
        "backend": [],
        "aicmo": [],
        "streamlit_pages": [],
        "tests": [],
        "other_tests": [],
    }

    # Backend modules
    for pyfile in (root / "backend").rglob("*.py"):
        if "__pycache__" not in str(pyfile) and "/.venv" not in str(pyfile):
            rel = pyfile.relative_to(root)
            if "tests" not in str(rel):
                structure["backend"].append(str(rel))

    # AICMO modules
    for pyfile in (root / "aicmo").rglob("*.py"):
        if "__pycache__" not in str(pyfile) and "/.venv" not in str(pyfile):
            rel = pyfile.relative_to(root)
            structure["aicmo"].append(str(rel))

    # Streamlit pages
    for pyfile in (root / "streamlit_pages").rglob("*.py"):
        if "__pycache__" not in str(pyfile):
            rel = pyfile.relative_to(root)
            structure["streamlit_pages"].append(str(rel))

    # Test modules
    for pyfile in (root / "tests").rglob("*.py"):
        if "__pycache__" not in str(pyfile):
            rel = pyfile.relative_to(root)
            structure["tests"].append(str(rel))

    for pyfile in (root / "backend" / "tests").rglob("*.py"):
        if "__pycache__" not in str(pyfile):
            rel = pyfile.relative_to(root)
            structure["other_tests"].append(str(rel))

    return structure


# ============================================================================
# PART 2: GENERATOR & WIRING AUDIT
# ============================================================================


def extract_section_generators():
    """Extract SECTION_GENERATORS from backend/main.py"""
    generators = {}
    main_py = Path("/workspaces/AICMO/backend/main.py").read_text()

    # Find SECTION_GENERATORS dict
    lines = main_py.split("\n")
    in_dict = False
    for i, line in enumerate(lines):
        if "SECTION_GENERATORS: dict" in line:
            in_dict = True
        elif in_dict:
            if line.strip().startswith("}"):
                break
            if ": " in line and "_gen_" in line:
                # Extract key: function
                parts = line.strip().split(": ")
                if len(parts) >= 2:
                    key = parts[0].strip("\"'")
                    func = parts[1].strip(",")
                    generators[key] = func

    return generators


def extract_package_presets():
    """Extract package sections from package_presets.py"""
    presets = {}
    presets_py = Path("/workspaces/AICMO/aicmo/presets/package_presets.py").read_text()

    try:
        tree = ast.parse(presets_py)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "PACKAGE_PRESETS":
                        # Extract dict value
                        if isinstance(node.value, ast.Dict):
                            for key_node, val_node in zip(node.value.keys, node.value.values):
                                if isinstance(key_node, ast.Constant):
                                    preset_key = key_node.value
                                    # Look for "sections" key
                                    if isinstance(val_node, ast.Dict):
                                        for sub_key_node, sub_val_node in zip(
                                            val_node.keys, val_node.values
                                        ):
                                            if (
                                                isinstance(sub_key_node, ast.Constant)
                                                and sub_key_node.value == "sections"
                                            ):
                                                if isinstance(sub_val_node, ast.List):
                                                    sections = []
                                                    for elem in sub_val_node.elts:
                                                        if isinstance(elem, ast.Constant):
                                                            sections.append(elem.value)
                                                    if sections:
                                                        presets[preset_key] = sections
    except Exception as e:
        print(f"Warning: Could not parse presets file: {e}")

    return presets


def extract_wow_rules():
    """Extract WOW_RULES from wow_rules.py"""
    rules = {}
    wow_py = Path("/workspaces/AICMO/aicmo/presets/wow_rules.py").read_text()

    try:
        tree = ast.parse(wow_py)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "WOW_RULES":
                        if isinstance(node.value, ast.Dict):
                            for key_node, val_node in zip(node.value.keys, node.value.values):
                                if isinstance(key_node, ast.Constant):
                                    wow_key = key_node.value
                                    # Extract sections list
                                    if isinstance(val_node, ast.Dict):
                                        for sub_key_node, sub_val_node in zip(
                                            val_node.keys, val_node.values
                                        ):
                                            if (
                                                isinstance(sub_key_node, ast.Constant)
                                                and sub_key_node.value == "sections"
                                            ):
                                                if isinstance(sub_val_node, ast.List):
                                                    sections = []
                                                    for elem in sub_val_node.elts:
                                                        if isinstance(elem, ast.Dict):
                                                            for k, v in zip(elem.keys, elem.values):
                                                                if (
                                                                    isinstance(k, ast.Constant)
                                                                    and k.value == "key"
                                                                ):
                                                                    if isinstance(v, ast.Constant):
                                                                        sections.append(v.value)
                                                    if sections:
                                                        rules[wow_key] = sections
    except Exception as e:
        print(f"Warning: Could not parse WOW rules: {e}")

    return rules


def extract_all_imports(file_path):
    """Extract all imported modules from a Python file"""
    imports = set()
    try:
        tree = ast.parse(Path(file_path).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
    except Exception:
        pass
    return imports


def find_all_python_files(directory):
    """Find all Python files in directory (excluding tests and venv)"""
    files = []
    try:
        for py in Path(directory).rglob("*.py"):
            if "__pycache__" not in str(py) and "/.venv" not in str(py) and "/tests" not in str(py):
                files.append(py)
    except Exception:
        pass
    return files


# ============================================================================
# PART 3: TEST COVERAGE ANALYSIS
# ============================================================================


def scan_test_files():
    """Scan all test files and extract test function names"""
    test_info = {}
    root = Path("/workspaces/AICMO")

    test_dirs = [root / "tests", root / "backend" / "tests"]

    for test_dir in test_dirs:
        if test_dir.exists():
            for test_file in test_dir.glob("test_*.py"):
                try:
                    content = test_file.read_text()
                    tree = ast.parse(content)

                    test_funcs = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                            test_funcs.append(node.name)

                    rel_path = str(test_file.relative_to(root))
                    test_info[rel_path] = test_funcs
                except Exception:
                    pass

    return test_info


def find_function_references(root_dir, target_func):
    """Find where a function is called/referenced"""
    references = []
    try:
        for py_file in find_all_python_files(root_dir):
            try:
                content = py_file.read_text()
                if target_func in content:
                    references.append(str(py_file.relative_to(Path(root_dir).parent)))
            except Exception:
                pass
    except Exception:
        pass
    return references


# ============================================================================
# PART 4: MAIN AUDIT
# ============================================================================


def main():
    print("\n" + "=" * 80)
    print("AICMO REPOSITORY STRUCTURE AUDIT")
    print("=" * 80)

    # 1. Map directories
    print("\n1. SCANNING DIRECTORY STRUCTURE...")
    structure = scan_directory_structure()
    print(f"   ✓ Backend modules: {len(structure['backend'])}")
    print(f"   ✓ AICMO modules: {len(structure['aicmo'])}")
    print(f"   ✓ Streamlit pages: {len(structure['streamlit_pages'])}")
    print(f"   ✓ Tests (root): {len(structure['tests'])}")
    print(f"   ✓ Tests (backend): {len(structure['other_tests'])}")

    # 2. Extract generators
    print("\n2. EXTRACTING GENERATORS & PRESETS...")
    generators = extract_section_generators()
    print(f"   ✓ SECTION_GENERATORS: {len(generators)} entries")

    presets = extract_package_presets()
    print(f"   ✓ PACKAGE_PRESETS: {len(presets)} packs")

    wow_rules = extract_wow_rules()
    print(f"   ✓ WOW_RULES: {len(wow_rules)} packs")

    # 3. Wiring audit
    print("\n3. WIRING AUDIT...")
    print("   Section presence check:")

    all_sections = set()
    all_preset_sections = set()
    all_wow_sections = set()

    for sections in presets.values():
        all_preset_sections.update(sections)

    for sections in wow_rules.values():
        all_wow_sections.update(sections)

    all_sections = all_preset_sections | all_wow_sections

    missing_in_generators = all_sections - set(generators.keys())
    unused_generators = set(generators.keys()) - all_sections

    print(f"   ✓ Total unique sections in presets: {len(all_preset_sections)}")
    print(f"   ✓ Total unique sections in WOW rules: {len(all_wow_sections)}")
    print(f"   ✓ Generators defined: {len(generators)}")

    if missing_in_generators:
        print(f"   ⚠ Missing in SECTION_GENERATORS ({len(missing_in_generators)}):")
        for s in sorted(missing_in_generators):
            print(f"      - {s}")

    if unused_generators:
        print(f"   ℹ Unused generators ({len(unused_generators)}):")
        for s in sorted(unused_generators)[:5]:
            print(f"      - {s}")
        if len(unused_generators) > 5:
            print(f"      ... and {len(unused_generators) - 5} more")

    # 4. Test coverage
    print("\n4. SCANNING TEST COVERAGE...")
    test_info = scan_test_files()
    total_tests = sum(len(v) for v in test_info.values())
    print(f"   ✓ Test files found: {len(test_info)}")
    print(f"   ✓ Total test functions: {total_tests}")

    print("\n   Test files summary:")
    for test_file, test_funcs in sorted(test_info.items())[:10]:
        print(f"      {test_file}: {len(test_funcs)} tests")

    if len(test_info) > 10:
        print(f"      ... and {len(test_info) - 10} more test files")

    # 5. Summary
    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(f"Backend modules:         {len(structure['backend'])}")
    print(f"AICMO modules:           {len(structure['aicmo'])}")
    print(f"Streamlit pages:         {len(structure['streamlit_pages'])}")
    print(f"Total Python test files: {len(test_info)}")
    print(f"Total test functions:    {total_tests}")
    print(f"\nSection generators:      {len(generators)} defined")
    print(f"Section coverage:        {len(all_preset_sections)} in presets")
    print(f"Missing generators:      {len(missing_in_generators)}")
    print(f"Unused generators:       {len(unused_generators)}")
    print("\n" + "=" * 80 + "\n")

    return {
        "structure": structure,
        "generators": generators,
        "presets": presets,
        "wow_rules": wow_rules,
        "test_info": test_info,
        "missing_generators": missing_in_generators,
        "unused_generators": unused_generators,
    }


if __name__ == "__main__":
    main()
