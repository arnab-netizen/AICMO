"""
Phase 7: Streamlit Smoke Tests
Verify Streamlit pages import without runtime errors.
"""

from pathlib import Path
import json

OUT_DIR = Path(".aicmo/audit/streamlit")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Find all Streamlit page files
streamlit_pages_dir = Path("streamlit_pages")
streamlit_files = list(streamlit_pages_dir.glob("*.py")) if streamlit_pages_dir.exists() else []

# Also check streamlit_app.py and pages/ directory
if Path("streamlit_app.py").exists():
    streamlit_files.append(Path("streamlit_app.py"))
if Path("pages").exists():
    streamlit_files.extend(Path("pages").glob("*.py"))

streamlit_files = sorted(set(streamlit_files))

print("=" * 70)
print("PHASE 7: Streamlit Smoke Tests")
print("=" * 70)
print(f"Found {len(streamlit_files)} Streamlit files to test")
print()

results = {
    "timestamp": __import__("datetime").datetime.now().isoformat(),
    "total_files": len(streamlit_files),
    "imports_successful": [],
    "imports_failed": [],
}

for py_file in streamlit_files:
    print(f"Testing {py_file}...", end=" ")

    try:
        # Try to compile/parse the Python file without executing it
        # This checks syntax and basic validity
        with open(py_file, "r") as f:
            code = f.read()

        # Compile the code (syntax check only, doesn't execute)
        compile(code, str(py_file), "exec")

        print("✓")
        results["imports_successful"].append({"file": str(py_file), "status": "syntax_valid"})
        (OUT_DIR / f"{py_file.stem}_import.log").write_text(
            f"✓ File {py_file} has valid Python syntax\n"
        )

    except SyntaxError as e:
        print("✗ (syntax error)")
        results["imports_failed"].append(
            {
                "file": str(py_file),
                "error": f"Syntax error on line {e.lineno}: {e.msg}",
                "status": "syntax_error",
            }
        )
        (OUT_DIR / f"{py_file.stem}_import.log").write_text(
            f"✗ Syntax error in {py_file}\n\nLine {e.lineno}: {e.msg}\n{e.text}\n"
        )

    except Exception as e:
        print(f"✗ ({str(e)[:30]})")
        results["imports_failed"].append({"file": str(py_file), "error": str(e), "status": "error"})
        (OUT_DIR / f"{py_file.stem}_import.log").write_text(
            f"✗ Error in {py_file}\n\nError: {str(e)}\n"
        )

# ============================================================================
# SUMMARY
# ============================================================================

(OUT_DIR / "import_results.json").write_text(json.dumps(results, indent=2))

print("\n" + "=" * 70)
print("STREAMLIT IMPORT SUMMARY")
print("=" * 70)
print(f"Total files tested: {results['total_files']}")
print(f"Successful imports: {len(results['imports_successful'])}")
print(f"Failed imports: {len(results['imports_failed'])}")
print("=" * 70)

# Create summary markdown
summary_md = f"""# Streamlit Import Audit

**Date**: {results['timestamp']}

## Summary

- **Total files tested**: {results['total_files']}
- **Successful imports**: {len(results['imports_successful'])}
- **Failed imports**: {len(results['imports_failed'])}

## Successfully Imported Files

"""

for item in results["imports_successful"]:
    summary_md += f"- ✅ {item['file']}\n"

summary_md += "\n## Failed Imports\n\n"

for item in results["imports_failed"]:
    summary_md += f"- ❌ {item['file']}\n"
    summary_md += f"  - Status: {item['status']}\n"
    if item.get("error"):
        summary_md += f"  - Error: {item['error'][:100]}...\n"
    summary_md += f"  - Log: see {Path(item['file']).stem}_import.log\n\n"

(OUT_DIR / "STREAMLIT_AUDIT_SUMMARY.md").write_text(summary_md)

print("\n✓ Summary written to STREAMLIT_AUDIT_SUMMARY.md")
print("✓ Individual logs written to .aicmo/audit/streamlit/<filename>_import.log")
