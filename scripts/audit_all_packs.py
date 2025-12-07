#!/usr/bin/env python3
"""
Comprehensive Pack Audit Script - Audits all 5 AICMO packs systematically.

Usage:
  python scripts/audit_all_packs.py [pack_key]
  
  If no pack_key provided, audits all packs in order:
  1. quick_social_basic
  2. strategy_campaign_standard
  3. launch_gtm_pack
  4. brand_turnaround_lab
  5. full_funnel_growth_suite

Output: Detailed audit report with PASS/FAIL for each section (A-I).
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.main import PACK_SECTION_WHITELIST
from backend.validators.pack_schemas import get_pack_schema
from backend.utils.benchmark_loader import (
    load_benchmarks_for_pack,
)


class PackAudit:
    """Comprehensive pack audit with sections A-I."""

    def __init__(self, pack_key: str):
        self.pack_key = pack_key
        self.results = {}
        self.todos = []

    def section_a_locate_and_map(self) -> Dict[str, Any]:
        """A. Locate and map the feature."""
        print(f"\n{'=' * 80}")
        print(f"[SECTION A] Locate & Map Feature: {self.pack_key}")
        print(f"{'=' * 80}")

        result = {
            "status": "PENDING",
            "files_found": [],
            "symbols_found": [],
            "gaps": [],
        }

        # Find whitelist entry
        if self.pack_key in PACK_SECTION_WHITELIST:
            whitelist = PACK_SECTION_WHITELIST[self.pack_key]
            result["files_found"].append("backend/main.py (PACK_SECTION_WHITELIST)")
            result["symbols_found"].append(
                f"PACK_SECTION_WHITELIST['{self.pack_key}'] = {{{len(whitelist)} sections}}"
            )

        # Find schema
        schema = get_pack_schema(self.pack_key)
        if schema:
            result["files_found"].append("backend/validators/pack_schemas.py")
            result["symbols_found"].append(f"PackSchema for {self.pack_key}")
        else:
            result["gaps"].append(f"No schema found for {self.pack_key}")

        # Check for benchmarks
        benchmark_path = (
            Path(__file__).parent.parent / "learning" / "benchmarks"
        ) / f"pack_{self.pack_key}*.json"
        benchmark_files = list(benchmark_path.parent.glob(f"pack_{self.pack_key}*.json"))
        if benchmark_files:
            result["files_found"].append(f"learning/benchmarks/ ({len(benchmark_files)} files)")
            for bf in benchmark_files:
                result["symbols_found"].append(f"Benchmark: {bf.name}")

        # Check for PDF template
        pdf_template_path = (
            Path(__file__).parent.parent / "backend" / "templates" / "pdf"
        ) / f"{self.pack_key}.html"
        if pdf_template_path.exists():
            result["files_found"].append(f"backend/templates/pdf/{self.pack_key}.html")
            result["symbols_found"].append("PDF HTML Template")
        else:
            result["gaps"].append(f"Missing PDF template: {self.pack_key}.html")

        # Check for tests
        tests_dir = Path(__file__).parent.parent / "backend" / "tests"
        test_files = list(tests_dir.glob(f"*{self.pack_key}*"))
        if test_files:
            result["files_found"].append(f"backend/tests/ ({len(test_files)} test files)")
            for tf in test_files:
                result["symbols_found"].append(f"Test: {tf.name}")

        result["status"] = "PASS" if not result["gaps"] else "FAIL"
        print(f"\n✅ Files Found ({len(result['files_found'])})")
        for f in result["files_found"]:
            print(f"  - {f}")

        if result["gaps"]:
            print(f"\n❌ Gaps Found ({len(result['gaps'])})")
            for gap in result["gaps"]:
                print(f"  - {gap}")
                self.todos.append(f"[A1] {self.pack_key}: {gap}")  # Add to todos

        print(f"\nStatus: {result['status']}")
        return result

    def section_b_wiring(self) -> Dict[str, Any]:
        """B. Check wiring from API/UI down to engine."""
        print(f"\n{'=' * 80}")
        print(f"[SECTION B] Wiring Check: {self.pack_key}")
        print(f"{'=' * 80}")

        result = {
            "status": "PENDING",
            "entry_point": None,
            "call_chain": [],
            "schema_match": False,
            "issues": [],
        }

        # Identify entry point
        result["entry_point"] = "api_aicmo_generate_report() in backend/main.py"

        # Check GenerateRequest has pack_key field
        result["call_chain"].append("Request validation: GenerateRequest.wow_package_key")

        # Check whitelist enforcement
        whitelist = PACK_SECTION_WHITELIST.get(self.pack_key, set())
        if whitelist:
            result["call_chain"].append(f"Whitelist enforcement: {len(whitelist)} allowed sections")
            result["schema_match"] = True
        else:
            result["issues"].append("Pack not in PACK_SECTION_WHITELIST")

        # Check schema validation
        schema = get_pack_schema(self.pack_key)
        if schema:
            required = schema.get("required_sections", [])
            result["call_chain"].append(f"Schema validation: {len(required)} required sections")
        else:
            result["issues"].append("Pack schema not found")

        result["status"] = "PASS" if not result["issues"] else "FAIL"

        print(f"\nEntry Point: {result['entry_point']}")
        print(f"Call Chain ({len(result['call_chain'])} steps):")
        for i, step in enumerate(result["call_chain"], 1):
            print(f"  {i}. {step}")

        if result["issues"]:
            print(f"\n❌ Issues ({len(result['issues'])})")
            for issue in result["issues"]:
                print(f"  - {issue}")
                self.todos.append(f"[B] {self.pack_key}: {issue}")

        print(f"\nStatus: {result['status']}")
        return result

    def section_c_config_and_templates(self) -> Dict[str, Any]:
        """C. Check configuration, presets, and templates."""
        print(f"\n{'=' * 80}")
        print(f"[SECTION C] Config & Templates: {self.pack_key}")
        print(f"{'=' * 80}")

        result = {
            "status": "PENDING",
            "config_items": [],
            "template_items": [],
            "registration": "PENDING",
            "issues": [],
        }

        # Check pack in registry
        if self.pack_key in PACK_SECTION_WHITELIST:
            result["registration"] = "PASS"
            sections = PACK_SECTION_WHITELIST[self.pack_key]
            result["config_items"].append(
                f"Pack registered in PACK_SECTION_WHITELIST with {len(sections)} sections"
            )
        else:
            result["registration"] = "FAIL"
            result["issues"].append("Pack not registered in PACK_SECTION_WHITELIST")

        # Check schema
        schema = get_pack_schema(self.pack_key)
        if schema:
            result["config_items"].append(
                f"Schema defined with {len(schema.get('required_sections', []))} required sections"
            )
        else:
            result["issues"].append("No pack schema defined")

        # Check template
        pdf_template = (
            Path(__file__).parent.parent / "backend" / "templates" / "pdf"
        ) / f"{self.pack_key}.html"
        if pdf_template.exists():
            result["template_items"].append(f"PDF template: {self.pack_key}.html")
        else:
            result["issues"].append(f"Missing PDF template: {self.pack_key}.html")

        # Check for brand-specific hardcoding in templates (sample check)
        if pdf_template.exists():
            with open(pdf_template) as f:
                content = f.read()
                if "example" in content.lower() or "acme" in content.lower():
                    result["issues"].append(
                        "⚠️  Possible hardcoded example brand in template (check manually)"
                    )

        result["status"] = (
            "PASS" if result["registration"] == "PASS" and not result["issues"] else "FAIL"
        )

        print(f"\nRegistration: {result['registration']}")
        print(f"Config Items ({len(result['config_items'])})")
        for item in result["config_items"]:
            print(f"  ✓ {item}")

        print(f"\nTemplate Items ({len(result['template_items'])})")
        for item in result["template_items"]:
            print(f"  ✓ {item}")

        if result["issues"]:
            print(f"\n❌ Issues ({len(result['issues'])})")
            for issue in result["issues"]:
                print(f"  - {issue}")
                self.todos.append(f"[C] {self.pack_key}: {issue}")

        print(f"\nStatus: {result['status']}")
        return result

    def section_d_tests_and_benchmarks(self) -> Dict[str, Any]:
        """D. Check tests and benchmark wiring."""
        print(f"\n{'=' * 80}")
        print(f"[SECTION D] Tests & Benchmarks: {self.pack_key}")
        print(f"{'=' * 80}")

        result = {
            "status": "PENDING",
            "test_files": [],
            "benchmark_files": [],
            "coverage_gaps": [],
        }

        # Find test files
        tests_dir = Path(__file__).parent.parent / "backend" / "tests"
        test_files = list(tests_dir.glob("*benchmark*.py")) + list(
            tests_dir.glob(f"*{self.pack_key.split('_')[0]}*.py")
        )
        result["test_files"] = [f.name for f in test_files if f.is_file()]

        # Find benchmark files
        benchmarks_dir = Path(__file__).parent.parent / "learning" / "benchmarks"
        benchmark_files = list(benchmarks_dir.glob(f"*{self.pack_key}*.json"))
        result["benchmark_files"] = [f.name for f in benchmark_files]

        # Load benchmark config to check wiring
        try:
            benchmark = load_benchmarks_for_pack(self.pack_key)
            if benchmark:
                result["coverage_gaps"].append("✓ Benchmark config loads successfully")
            else:
                result["coverage_gaps"].append("⚠️  Benchmark config is empty")
        except Exception as e:
            result["coverage_gaps"].append(f"❌ Cannot load benchmark: {e}")

        result["status"] = "PASS" if result["test_files"] else "PARTIAL"

        print(f"\nTest Files ({len(result['test_files'])})")
        for tf in result["test_files"]:
            print(f"  - {tf}")

        print(f"\nBenchmark Files ({len(result['benchmark_files'])})")
        for bf in result["benchmark_files"]:
            print(f"  - {bf}")

        print("\nCoverage Assessment:")
        for gap in result["coverage_gaps"]:
            print(f"  {gap}")

        # Suggest missing tests
        if not any("pack" in tf.lower() for tf in result["test_files"]):
            msg = f"Missing comprehensive pack-level test for {self.pack_key}"
            result["coverage_gaps"].append(msg)
            self.todos.append(f"[D] {msg}")

        print(f"\nStatus: {result['status']}")
        return result

    def section_e_validation_scripts(self) -> Dict[str, Any]:
        """E. Identify and inspect validation commands."""
        print(f"\n{'=' * 80}")
        print(f"[SECTION E] Validation Scripts: {self.pack_key}")
        print(f"{'=' * 80}")

        result = {
            "status": "PENDING",
            "commands": [],
            "scripts": [],
        }

        # Common validation commands
        result["commands"].append(
            f"pytest backend/tests/test_benchmark_enforcement_smoke.py -k {self.pack_key} -v"
        )
        result["commands"].append(f"python backend/debug/print_benchmark_issues.py {self.pack_key}")

        # Find validation scripts
        scripts_dir = Path(__file__).parent.parent / "scripts"
        dev_scripts = list(scripts_dir.glob("dev_*.py"))
        result["scripts"] = [s.name for s in dev_scripts]

        result["status"] = "PASS"

        print("\nRecommended Test Commands:")
        for i, cmd in enumerate(result["commands"], 1):
            print(f"  {i}. {cmd}")

        print(f"\nAvailable Validation Scripts ({len(result['scripts'])})")
        for script in result["scripts"][:5]:  # Show first 5
            print(f"  - {script}")

        print(f"\nStatus: {result['status']}")
        return result

    def section_f_output_structure(self) -> Dict[str, Any]:
        """F. Output structure & correctness vs expectations."""
        print(f"\n{'=' * 80}")
        print(f"[SECTION F] Output Structure: {self.pack_key}")
        print(f"{'=' * 80}")

        result = {
            "status": "PENDING",
            "required_sections": [],
            "quality_checks": [],
            "gaps": [],
        }

        # Get schema
        schema = get_pack_schema(self.pack_key)
        if schema:
            required = schema.get("required_sections", [])
            result["required_sections"] = required
            print(f"\nRequired Sections ({len(required)}):")
            for i, sec in enumerate(required, 1):
                print(f"  {i}. {sec}")
        else:
            result["gaps"].append("No schema defined")

        # Quality expectations
        quality_checks = [
            "✓ No stub/placeholder content",
            "✓ All sections non-empty (>50 chars)",
            "✓ Markdown properly formatted",
            "✓ No hardcoded brand examples (generic)",
            "✓ Consistent tone and structure",
            "✓ No truncated sections (<90% expected)",
        ]
        result["quality_checks"] = quality_checks

        print("\nQuality Expectations:")
        for check in quality_checks:
            print(f"  {check}")

        # Check if tests enforce these
        benchmark = load_benchmarks_for_pack(self.pack_key)
        if benchmark:
            print("\n✓ Benchmark config exists with validation rules")
        else:
            result["gaps"].append("No benchmark config to enforce quality expectations")

        result["status"] = "PASS" if schema and benchmark else "PARTIAL"

        if result["gaps"]:
            print("\n⚠️  Gaps:")
            for gap in result["gaps"]:
                print(f"  - {gap}")
                self.todos.append(f"[F] {self.pack_key}: {gap}")

        print(f"\nStatus: {result['status']}")
        return result

    def section_g_export_wiring(self) -> Dict[str, Any]:
        """G. PDF/PPTX/export wiring (if applicable)."""
        print(f"\n{'=' * 80}")
        print(f"[SECTION G] PDF/PPTX Export: {self.pack_key}")
        print(f"{'=' * 80}")

        result = {
            "status": "PENDING",
            "export_template": None,
            "wiring_checks": [],
            "issues": [],
        }

        # Check PDF template
        pdf_path = (
            Path(__file__).parent.parent / "backend" / "templates" / "pdf"
        ) / f"{self.pack_key}.html"
        if pdf_path.exists():
            result["export_template"] = f"{self.pack_key}.html"
            result["wiring_checks"].append("✓ PDF template exists")
        else:
            result["issues"].append("❌ Missing PDF template")

        # Check export_utils registration
        export_utils_path = Path(__file__).parent.parent / "backend" / "export_utils.py"
        if export_utils_path.exists():
            with open(export_utils_path) as f:
                content = f.read()
                if self.pack_key in content:
                    result["wiring_checks"].append("✓ Pack referenced in export_utils.py")
                else:
                    result["issues"].append("⚠️  Pack not found in export_utils.py")

        # Check pdf_renderer registration
        pdf_renderer_path = Path(__file__).parent.parent / "backend" / "pdf_renderer.py"
        if pdf_renderer_path.exists():
            with open(pdf_renderer_path) as f:
                content = f.read()
                if self.pack_key in content:
                    result["wiring_checks"].append("✓ Pack referenced in pdf_renderer.py")
                else:
                    result["issues"].append("⚠️  Pack not found in pdf_renderer.py")

        result["status"] = "PASS" if not result["issues"] else "FAIL"

        print(f"\nExport Template: {result['export_template']}")
        print(f"\nWiring Checks ({len(result['wiring_checks'])})")
        for check in result["wiring_checks"]:
            print(f"  {check}")

        if result["issues"]:
            print(f"\n❌ Issues ({len(result['issues'])})")
            for issue in result["issues"]:
                print(f"  {issue}")
                self.todos.append(f"[G] {self.pack_key}: {issue}")

        print(f"\nStatus: {result['status']}")
        return result

    def section_h_error_handling(self) -> Dict[str, Any]:
        """H. Error handling & logging."""
        print(f"\n{'=' * 80}")
        print(f"[SECTION H] Error Handling: {self.pack_key}")
        print(f"{'=' * 80}")

        result = {
            "status": "PENDING",
            "error_checks": [],
            "logging_checks": [],
            "gaps": [],
        }

        # Check for error handling in main.py
        main_path = Path(__file__).parent.parent / "backend" / "main.py"
        with open(main_path) as f:
            content = f.read()
            if "except" in content and "logger" in content:
                result["error_checks"].append("✓ Try/except blocks present")
                result["logging_checks"].append("✓ Logger usage detected")
            else:
                result["gaps"].append("⚠️  May be missing error handling")

        # Check for pack-specific error handling
        if f'"{self.pack_key}"' in content or f"'{self.pack_key}'" in content:
            result["error_checks"].append("✓ Pack-specific code present")
        else:
            result["gaps"].append("⚠️  No pack-specific error handling")

        result["status"] = "PASS"

        print(f"\nError Handling Checks ({len(result['error_checks'])})")
        for check in result["error_checks"]:
            print(f"  {check}")

        print(f"\nLogging Checks ({len(result['logging_checks'])})")
        for check in result["logging_checks"]:
            print(f"  {check}")

        if result["gaps"]:
            print("\n⚠️  Potential Gaps:")
            for gap in result["gaps"]:
                print(f"  {gap}")
                self.todos.append(f"[H] {gap}")

        print(f"\nStatus: {result['status']}")
        return result

    def section_i_final_summary(self) -> Dict[str, Any]:
        """I. Final summary for this feature."""
        print(f"\n{'=' * 80}")
        print(f"[SECTION I] Final Summary: {self.pack_key}")
        print(f"{'=' * 80}")

        # Collect all statuses
        statuses = {
            "A": self.results.get("A", {}).get("status", "UNKNOWN"),
            "B": self.results.get("B", {}).get("status", "UNKNOWN"),
            "C": self.results.get("C", {}).get("status", "UNKNOWN"),
            "D": self.results.get("D", {}).get("status", "UNKNOWN"),
            "E": self.results.get("E", {}).get("status", "UNKNOWN"),
            "F": self.results.get("F", {}).get("status", "UNKNOWN"),
            "G": self.results.get("G", {}).get("status", "UNKNOWN"),
            "H": self.results.get("H", {}).get("status", "UNKNOWN"),
        }

        pass_count = sum(1 for s in statuses.values() if s == "PASS")
        fail_count = sum(1 for s in statuses.values() if s == "FAIL")

        overall_status = "PASS" if fail_count == 0 else "FAIL" if fail_count > 2 else "PARTIAL"

        result = {
            "pack_key": self.pack_key,
            "completeness": overall_status,
            "wiring_correctness": statuses.get("B", "UNKNOWN"),
            "output_correctness": statuses.get("F", "UNKNOWN"),
            "section_scores": statuses,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "todos": self.todos,
        }

        print("\n📊 Section Scores:")
        for section, status in statuses.items():
            icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            print(f"  {icon} [{section}] {status}")

        print("\n📈 Summary:")
        print(f"  PASSED: {pass_count}/8 sections")
        print(f"  FAILED: {fail_count}/8 sections")
        print(f"  Overall: {overall_status}")

        if self.todos:
            print(f"\n📋 TODOs ({len(self.todos)})")
            for i, todo in enumerate(self.todos, 1):
                print(f"  {i}. {todo}")

        print(f"\nStatus: {overall_status}")
        return result

    def run_full_audit(self) -> Dict[str, Any]:
        """Run all sections A-I."""
        self.results["A"] = self.section_a_locate_and_map()
        self.results["B"] = self.section_b_wiring()
        self.results["C"] = self.section_c_config_and_templates()
        self.results["D"] = self.section_d_tests_and_benchmarks()
        self.results["E"] = self.section_e_validation_scripts()
        self.results["F"] = self.section_f_output_structure()
        self.results["G"] = self.section_g_export_wiring()
        self.results["H"] = self.section_h_error_handling()
        final = self.section_i_final_summary()

        return {
            "pack_key": self.pack_key,
            "sections": self.results,
            "final_summary": final,
            "all_todos": self.todos,
        }


def main():
    """Run audit for specified pack(s)."""
    packs_to_audit = [
        "quick_social_basic",
        "strategy_campaign_standard",
        "launch_gtm_pack",
        "brand_turnaround_lab",
        "full_funnel_growth_suite",
    ]

    # If specific pack provided, audit only that one
    if len(sys.argv) > 1:
        packs_to_audit = [sys.argv[1]]

    all_results = []

    for pack_key in packs_to_audit:
        print(f"\n\n{'#' * 80}")
        print(f"# AUDITING PACK: {pack_key}")
        print(f"{'#' * 80}")

        auditor = PackAudit(pack_key)
        result = auditor.run_full_audit()
        all_results.append(result)

    # Summary across all packs
    print(f"\n\n{'=' * 80}")
    print("CONSOLIDATED SUMMARY - ALL PACKS")
    print(f"{'=' * 80}\n")

    for result in all_results:
        final = result["final_summary"]
        print(
            f"{final['pack_key']:30s} | Completeness: {final['completeness']:8s} | "
            f"Passed: {final['pass_count']}/8 | TODOs: {len(final['todos'])}"
        )

    # Export detailed results to JSON
    output_path = Path(__file__).parent.parent / "audit_results.json"
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n✅ Detailed results saved to: {output_path}")


if __name__ == "__main__":
    main()
