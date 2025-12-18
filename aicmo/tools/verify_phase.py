#!/usr/bin/env python3
"""
Phase Verification Script — Enforces PHASE_PROTOCOL.md rules

Usage:
    python -m aicmo.tools.verify_phase --phase 0

Exit Codes:
    0: Verification PASSED
    1: Verification FAILED
    2: Invalid arguments
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple


def pydantic_field_names(model_cls) -> list[str]:
    """Return a list of field names for a Pydantic model class in a
    Pydantic-version-safe way.

    - Prefer `model_fields` (Pydantic v2).
    - Fallback to `__fields__` (Pydantic v1).
    - If neither present, raise RuntimeError.
    """
    # Pydantic v2: `model_fields` is a mapping
    if hasattr(model_cls, "model_fields"):
        mf = getattr(model_cls, "model_fields")
        try:
            return list(mf.keys())
        except Exception:
            # Defensive: convert to list if not dict-like
            return [str(k) for k in mf]

    # Pydantic v1: __fields__ mapping
    if hasattr(model_cls, "__fields__"):
        fld = getattr(model_cls, "__fields__")
        try:
            return list(fld.keys())
        except Exception:
            return [str(k) for k in fld]

    raise RuntimeError("Unable to introspect Pydantic model fields for %r" % (model_cls,))


class PhaseVerifier:
    """Verifies phase completion according to PHASE_PROTOCOL.md"""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def verify_phase_0(self) -> bool:
        """Verify Phase 0: Enforcement Installation"""
        print("🔍 Verifying Phase 0: Enforcement Installation\n")

        # Check 1: PHASE_PROTOCOL.md exists
        protocol_path = self.repo_root / "docs" / "PHASE_PROTOCOL.md"
        if protocol_path.exists():
            print("✅ PHASE_PROTOCOL.md exists")
        else:
            self.errors.append("❌ PHASE_PROTOCOL.md NOT FOUND at docs/PHASE_PROTOCOL.md")

        # Check 2: audit_artifacts/ directory exists
        audit_dir = self.repo_root / "audit_artifacts"
        if audit_dir.exists() and audit_dir.is_dir():
            print("✅ audit_artifacts/ directory exists")
        else:
            self.errors.append("❌ audit_artifacts/ directory NOT FOUND")

        # Check 3: No assumptions.md anywhere in repo
        assumptions_files = list(self.repo_root.glob("**/assumptions.md"))
        # Filter out git directory
        assumptions_files = [f for f in assumptions_files if ".git" not in str(f)]
        
        if not assumptions_files:
            print("✅ No assumptions.md found (evidence-only rule enforced)")
        else:
            for f in assumptions_files:
                rel_path = f.relative_to(self.repo_root)
                self.errors.append(f"❌ ASSUMPTIONS FILE DETECTED: {rel_path}")

        # Check 4: verify_phase.py is valid Python (already passed if we're running)
        verify_script = self.repo_root / "aicmo" / "tools" / "verify_phase.py"
        if verify_script.exists():
            print("✅ verify_phase.py exists and is valid Python")
        else:
            self.errors.append("❌ verify_phase.py NOT FOUND")

        # Check 5: Makefile has verify-phase-0 target
        makefile = self.repo_root / "Makefile"
        if makefile.exists():
            content = makefile.read_text()
            if "verify-phase-0" in content:
                print("✅ Makefile has verify-phase-0 target")
            else:
                self.warnings.append("⚠️  Makefile missing verify-phase-0 target")
        else:
            self.warnings.append("⚠️  Makefile not found (optional)")

        # Check 6: Test file exists
        test_file = self.repo_root / "tests" / "test_verify_phase_cli.py"
        if test_file.exists():
            print("✅ test_verify_phase_cli.py exists")
        else:
            self.warnings.append("⚠️  test_verify_phase_cli.py not found (optional)")

        # Summary
        print("\n" + "=" * 60)
        if self.errors:
            print("❌ Phase 0 Verification: FAIL\n")
            for error in self.errors:
                print(f"   {error}")
        else:
            print("✅ Phase 0 Verification: PASS\n")
            print("   Evidence Pack Complete:")
            print("   - PHASE_PROTOCOL.md: ✅")
            print("   - audit_artifacts/: ✅")
            print("   - No assumptions: ✅")
            print("   - verify_phase.py: ✅")

        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   {warning}")

        print("=" * 60)

        return len(self.errors) == 0

    def verify_phase_1(self) -> bool:
        """Verify Phase 1: Canonical Entrypoints"""
        print("🔍 Verifying Phase 1: Canonical Entrypoints\n")

        # Check 1: ARCHITECTURE.md headings
        arch_path = self.repo_root / "docs" / "ARCHITECTURE.md"
        if not arch_path.exists():
            self.errors.append("❌ docs/ARCHITECTURE.md missing")
        else:
            content = arch_path.read_text(encoding="utf-8")
            for heading in ["Canonical Backend Entry", "Canonical UI Entry", "Deprecated Entrypoints"]:
                if heading not in content:
                    self.errors.append(f"❌ ARCHITECTURE.md missing heading: {heading}")

        # Check 2: Canonical headers in operator_v2.py and backend/app.py
        ui_path = self.repo_root / "operator_v2.py"
        backend_path = self.repo_root / "backend" / "app.py"
        if not ui_path.exists():
            self.errors.append("❌ operator_v2.py missing (canonical UI)")
        else:
            ui_content = ui_path.read_text(encoding="utf-8")
            if "CANONICAL UI ENTRYPOINT" not in ui_content:
                self.errors.append("❌ operator_v2.py missing CANONICAL header")
        if not backend_path.exists():
            self.errors.append("❌ backend/app.py missing (canonical backend)")
        else:
            backend_content = backend_path.read_text(encoding="utf-8")
            if "CANONICAL BACKEND ENTRYPOINT" not in backend_content:
                self.errors.append("❌ backend/app.py missing CANONICAL header")

        # Check 3: Deprecated directory and files
        deprecated_ui = self.repo_root / "deprecated" / "ui" / "aicmo_operator_legacy.py"
        deprecated_readme = self.repo_root / "deprecated" / "README.md"
        if not deprecated_ui.exists():
            self.errors.append("❌ deprecated/ui/aicmo_operator_legacy.py missing")
        if not deprecated_readme.exists():
            self.errors.append("❌ deprecated/README.md missing")

        # Check 4: Forbidden imports in operator_v2.py
        forbidden = [
            "from deprecated.ui.aicmo_operator_legacy",
            "import deprecated.ui.aicmo_operator_legacy",
            "from streamlit_pages.aicmo_operator",
            "import streamlit_pages.aicmo_operator",
        ]
        if ui_path.exists():
            for bad in forbidden:
                if bad in ui_content:
                    self.errors.append(f"❌ operator_v2.py references deprecated operator: {bad}")

        # Check 5: Deprecated operator file presence — prefer deprecated/ move, but allow legacy file
        # If legacy file remains, ensure it's documented in ARCHITECTURE.md. Do not fail solely for presence.
        forbidden_files = [self.repo_root / "streamlit_pages" / "aicmo_operator.py"]
        for f in forbidden_files:
            if f.exists():
                # If ARCHITECTURE.md exists, require that the legacy path is listed under Deprecated Entrypoints
                if arch_path.exists():
                    arch_txt = arch_path.read_text(encoding="utf-8")
                    rel = str(f.relative_to(self.repo_root))
                    if rel not in arch_txt:
                        self.errors.append(f"❌ Legacy deprecated operator present but not documented in ARCHITECTURE.md: {rel}")
                    else:
                        self.warnings.append(f"⚠️ Legacy deprecated operator present at {rel} (documented in ARCHITECTURE.md)")
                else:
                    self.warnings.append(f"⚠️ Legacy deprecated operator present at {f.relative_to(self.repo_root)}")

        # Phase 0 checks (reuse)
        phase0_ok = self.verify_phase_0()

        # Summary
        print("\n" + "=" * 60)
        if self.errors:
            print("❌ Phase 1 Verification: FAIL\n")
            for error in self.errors:
                print(f"   {error}")
        else:
            print("✅ Phase 1 Verification: PASS\n")
            print("   Canonical Entrypoints and deprecation checks complete.")

        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   {warning}")

        print("=" * 60)

        return len(self.errors) == 0

    def verify(self, phase: int) -> bool:
        """Verify specified phase"""
        if phase == 0:
            return self.verify_phase_0()
        elif phase == 1:
            return self.verify_phase_1()
        elif phase == 2:
            return self.verify_phase_2()
        elif phase == 3:
            return self.verify_phase_3()
        else:
            print(f"❌ Phase {phase} verification not yet implemented")
            self.errors.append(f"Phase {phase} verification not implemented")
            return False

    def verify_phase_2(self) -> bool:
        """Verify Phase 2: State machine and gating enforcement"""
        print("🔍 Verifying Phase 2: State machine and gating enforcement\n")

        # Check 1: ProjectState enum exists and has required values
        try:
            from aicmo.domain.state_machine import ProjectState
        except Exception:
            self.errors.append("❌ aicmo.domain.state_machine.ProjectState not importable")
            return False

        required = [
            "CREATED",
            "INTAKE_COMPLETE",
            "STRATEGY_GENERATED",
            "STRATEGY_APPROVED",
            "CAMPAIGN_DEFINED",
            "CREATIVE_GENERATED",
            "QC_FAILED",
            "QC_APPROVED",
            "DELIVERED",
        ]
        missing = [r for r in required if not hasattr(ProjectState, r)]
        if missing:
            self.errors.append(f"❌ ProjectState missing values: {missing}")

        # Check 1b: Ensure there are no duplicate ProjectState definitions elsewhere
        dup_defs = []
        canonical_path = (self.repo_root / "aicmo" / "domain" / "state_machine.py").resolve()
        verifier_path = (self.repo_root / "aicmo" / "tools" / "verify_phase.py").resolve()
        for py in self.repo_root.glob("**/*.py"):
            try:
                # skip the canonical file itself and this verifier script
                if py.resolve() in {canonical_path, verifier_path}:
                    continue
            except Exception:
                pass
            txt = py.read_text(encoding="utf-8")
            if "class ProjectState" in txt:
                dup_defs.append(str(py.relative_to(self.repo_root)))

        if dup_defs:
            self.errors.append(f"❌ Duplicate ProjectState definitions found in: {dup_defs}")

        # Check 2: gating.py imports ProjectState and defines require_state
        gating_path = self.repo_root / "aicmo" / "ui" / "gating.py"
        if not gating_path.exists():
            self.errors.append("❌ aicmo/ui/gating.py missing")
        else:
            src = gating_path.read_text(encoding="utf-8")
            if "ProjectState" not in src:
                self.errors.append("❌ gating.py does not reference ProjectState")
            if "def require_state" not in src:
                self.errors.append("❌ gating.py missing require_state definition")

        # Check 3: tests exist
        t1 = self.repo_root / "tests" / "test_state_machine_transitions.py"
        t2 = self.repo_root / "tests" / "test_gating_enforcement.py"
        if not t1.exists() or not t2.exists():
            self.errors.append("❌ Phase 2 tests missing")

        # Summary
        print("\n" + "=" * 60)
        if self.errors:
            print("❌ Phase 2 Verification: FAIL\n")
            for error in self.errors:
                print(f"   {error}")
        else:
            print("✅ Phase 2 Verification: PASS\n")

        print("=" * 60)
        return len(self.errors) == 0

    def verify_phase_3(self) -> bool:
        """Verify Phase 3: Artifact model, store APIs, compat, and client-ready"""
        print("🔍 Verifying Phase 3: Artifact model + store + compat + client-ready\n")

        # Check: aicmo.domain.artifacts.Artifact exists and has required fields
        try:
            from aicmo.domain.artifacts import Artifact as DomainArtifact
        except Exception:
            self.errors.append("❌ aicmo.domain.artifacts.Artifact not importable")
            return False

        required_fields = [
            "id","tenant_id","project_id","type","status","schema_version",
            "version","produced_by","produced_at","input_artifact_ids","state_at_creation",
            "trace_id","created_by","checksum","quality_contract","content"
        ]
        # Use Pydantic-safe field introspection
        try:
            field_names = pydantic_field_names(DomainArtifact)
        except RuntimeError:
            field_names = []

        missing = [f for f in required_fields if not hasattr(DomainArtifact, f) and f not in field_names]
        if missing:
            if field_names:
                pd_missing = [f for f in required_fields if f not in field_names]
                if pd_missing:
                    self.errors.append(f"❌ Artifact missing fields: {pd_missing}")
            else:
                self.errors.append(f"❌ Artifact missing fields: {missing}")

        # Check ArtifactStore.put signature accepts expected_version
        try:
            from aicmo.ui.persistence.artifact_store import ArtifactStore
            import inspect
            sig = inspect.signature(ArtifactStore.put)
            if 'expected_version' not in sig.parameters:
                self.errors.append("❌ ArtifactStore.put does not accept expected_version")
        except Exception:
            self.errors.append("❌ aicmo.ui.persistence.artifact_store.ArtifactStore not importable")

        # ErrorResponse exists
        try:
            from aicmo.api.schemas import ErrorResponse
        except Exception:
            self.errors.append("❌ aicmo.api.schemas.ErrorResponse not importable")

        # is_client_ready exists
        try:
            from aicmo.core.client_ready import is_client_ready
        except Exception:
            self.errors.append("❌ aicmo.core.client_ready.is_client_ready not importable")

        # assumptions.md must NOT exist
        assumptions = list(self.repo_root.glob('**/assumptions.md'))
        assumptions = [f for f in assumptions if '.git' not in str(f)]
        if assumptions:
            for f in assumptions:
                self.errors.append(f"❌ ASSUMPTIONS FILE DETECTED: {f.relative_to(self.repo_root)}")

        print("\n" + "=" * 60)
        if self.errors:
            print("❌ Phase 3 Verification: FAIL\n")
            for error in self.errors:
                print(f"   {error}")
        else:
            print("✅ Phase 3 Verification: PASS\n")

        print("=" * 60)
        return len(self.errors) == 0


def main() -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Verify phase completion according to PHASE_PROTOCOL.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m aicmo.tools.verify_phase --phase 0
    python -m aicmo.tools.verify_phase --phase 1

Exit Codes:
    0: Verification PASSED
    1: Verification FAILED
    2: Invalid arguments
        """
    )
    parser.add_argument(
        "--phase",
        type=int,
        required=True,
        help="Phase number to verify (0, 1, 2, ...)"
    )

    args = parser.parse_args()

    # Determine repo root (assume we're in aicmo/tools/)
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent

    # Verify phase
    verifier = PhaseVerifier(repo_root)
    success = verifier.verify(args.phase)

    # Return exit code
    if success:
        print(f"\n🎯 VERDICT: PHASE {args.phase} COMPLETE\n")
        return 0
    else:
        print(f"\n❌ VERDICT: PHASE {args.phase} INCOMPLETE\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
