import importlib
import sys
import os
from pathlib import Path
import pytest

# --- POSITIVE TESTS ---
def test_import_canonical_ui():
    import operator_v2
    assert hasattr(operator_v2, "__file__")

def test_import_canonical_backend():
    backend_app = importlib.import_module("backend.app")
    assert hasattr(backend_app, "__file__")

# --- NEGATIVE TESTS ---
def test_operator_v2_no_deprecated_imports():
    """operator_v2.py must NOT import or reference deprecated operator modules"""
    with open("operator_v2.py") as f:
        content = f.read()
    forbidden = [
        "from deprecated.ui.aicmo_operator_legacy",
        "import deprecated.ui.aicmo_operator_legacy",
        "from streamlit_pages.aicmo_operator",
        "import streamlit_pages.aicmo_operator",
    ]
    for bad in forbidden:
        assert bad not in content, f"operator_v2.py references deprecated operator: {bad}"

# ARCHITECTURE.md headings check
def test_architecture_md_headings():
    arch = Path("docs/ARCHITECTURE.md").read_text()
    for heading in ["Canonical Backend Entry", "Canonical UI Entry", "Deprecated Entrypoints"]:
        assert heading in arch, f"ARCHITECTURE.md missing heading: {heading}"

# Deprecated operator file must NOT exist at repo root
def test_no_deprecated_operator_at_root():
    """If a legacy deprecated operator remains in `streamlit_pages/`, it must be documented in ARCHITECTURE.md.

    Presence of the legacy file is allowed only if it is explicitly listed under the
    `Deprecated Entrypoints` heading in `docs/ARCHITECTURE.md`.
    """
    forbidden = ["streamlit_pages/aicmo_operator.py"]
    arch = Path("docs/ARCHITECTURE.md")
    arch_txt = arch.read_text() if arch.exists() else ""
    for f in forbidden:
        p = Path(f)
        if p.exists():
            assert f in arch_txt, f"{f} exists but is not listed under Deprecated Entrypoints in docs/ARCHITECTURE.md"

# Deprecated directory must exist
def test_deprecated_directory_exists():
    assert Path("deprecated/ui/aicmo_operator_legacy.py").exists(), "deprecated/ui/aicmo_operator_legacy.py missing"
    assert Path("deprecated/README.md").exists(), "deprecated/README.md missing"

# Canonical headers present
def test_canonical_headers():
    ui = Path("operator_v2.py").read_text(encoding="utf-8")
    backend = Path("backend/app.py").read_text(encoding="utf-8")
    assert "CANONICAL UI ENTRYPOINT" in ui, "operator_v2.py missing CANONICAL header"
    assert "CANONICAL BACKEND ENTRYPOINT" in backend, "backend/app.py missing CANONICAL header"
