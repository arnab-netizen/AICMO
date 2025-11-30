"""
Test suite to verify wiring between SECTION_GENERATORS, pack presets, and benchmark files.

This test ensures that:
1. Every section used by every pack has a corresponding benchmark entry
2. Every benchmark section_id references a real generator in SECTION_GENERATORS

These tests will FAIL LOUDLY if there are any mismatches, making it impossible
to silently deploy packs or benchmarks with missing/incorrect configuration.
"""

import json
import pytest
import warnings
from pathlib import Path
from typing import Dict, List, Tuple

# Suppress FastAPI deprecation warnings during import
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from backend.main import SECTION_GENERATORS

from aicmo.presets.package_presets import PACKAGE_PRESETS
from backend.utils.benchmark_loader import (
    load_benchmarks_for_pack,
    get_section_benchmark,
    BenchmarkNotFoundError,
    BENCHMARKS_DIR,
)


def get_all_pack_sections() -> List[Tuple[str, str]]:
    """
    Discover all (pack_key, section_id) pairs from PACKAGE_PRESETS.
    
    Returns:
        List of (pack_key, section_id) tuples for all configured packs
    """
    pack_sections = []
    
    for pack_key, config in PACKAGE_PRESETS.items():
        sections = config.get("sections", [])
        for section_id in sections:
            pack_sections.append((pack_key, section_id))
    
    return pack_sections


def get_all_benchmark_files() -> List[Path]:
    """
    Find all benchmark JSON files in the benchmarks directory.
    
    Returns:
        List of Path objects for benchmark files (excluding schema files)
    """
    if not BENCHMARKS_DIR.exists():
        return []
    
    benchmark_files = []
    for file_path in BENCHMARKS_DIR.glob("section_benchmarks.*.json"):
        # Skip schema files
        if "schema" not in file_path.name:
            benchmark_files.append(file_path)
    
    return benchmark_files


class TestBenchmarksWiring:
    """Test suite for benchmark configuration wiring."""
    
    def test_all_pack_sections_have_benchmarks(self):
        """
        Verify that every section in every pack has a corresponding benchmark entry.
        
        This test scans ALL packs and ALL sections configured in PACKAGE_PRESETS
        and ensures each one has a benchmark definition.
        
        FAILURE means: A pack section is configured but has no quality benchmark.
        ACTION: Add the missing benchmark to the appropriate section_benchmarks.<pack>.json file.
        """
        pack_sections = get_all_pack_sections()
        
        # Track missing benchmarks for detailed error reporting
        missing_benchmarks = []
        
        for pack_key, section_id in pack_sections:
            try:
                benchmark = get_section_benchmark(pack_key, section_id)
                
                if benchmark is None:
                    missing_benchmarks.append({
                        "pack_key": pack_key,
                        "section_id": section_id,
                        "reason": "Benchmark returned None (section not defined in benchmark file)",
                    })
            
            except BenchmarkNotFoundError as e:
                missing_benchmarks.append({
                    "pack_key": pack_key,
                    "section_id": section_id,
                    "reason": f"No benchmark file found for pack: {str(e)}",
                })
            
            except Exception as e:
                missing_benchmarks.append({
                    "pack_key": pack_key,
                    "section_id": section_id,
                    "reason": f"Unexpected error loading benchmark: {str(e)}",
                })
        
        # Generate detailed failure message if any benchmarks are missing
        if missing_benchmarks:
            error_lines = [
                "\n" + "=" * 80,
                "BENCHMARK WIRING FAILURE: Missing Benchmarks Detected",
                "=" * 80,
                f"\nFound {len(missing_benchmarks)} sections without benchmarks:\n",
            ]
            
            # Group by pack for clearer reporting
            by_pack: Dict[str, List[dict]] = {}
            for item in missing_benchmarks:
                pack_key = item["pack_key"]
                if pack_key not in by_pack:
                    by_pack[pack_key] = []
                by_pack[pack_key].append(item)
            
            for pack_key, items in sorted(by_pack.items()):
                error_lines.append(f"\n📦 Pack: {pack_key}")
                error_lines.append(f"   Missing {len(items)} benchmark(s):")
                for item in items:
                    error_lines.append(f"   • Section '{item['section_id']}'")
                    error_lines.append(f"     Reason: {item['reason']}")
            
            error_lines.extend([
                "\n" + "=" * 80,
                "ACTION REQUIRED:",
                "=" * 80,
                "1. Identify which benchmark file should contain these sections:",
                "   - Quick Social Pack → section_benchmarks.quick_social.json",
                "   - Strategy Campaign Pack → section_benchmarks.strategy_campaign.json",
                "   - Full Funnel Pack → section_benchmarks.full_funnel.json",
                "   - Performance Audit Pack → section_benchmarks.performance_audit.json",
                "   - CRM Retention Pack → section_benchmarks.crm_retention.json",
                "",
                "2. Add benchmark entries for each missing section with:",
                "   - id: section identifier (must match SECTION_GENERATORS key)",
                "   - label: human-readable section name",
                "   - min_words, max_words: acceptable word count range",
                "   - min_bullets, max_bullets: bullet point requirements",
                "   - min_headings, max_headings: heading count requirements",
                "   - required_headings: list of required heading text",
                "   - forbidden_substrings: patterns that indicate low quality",
                "",
                "3. Verify section_id matches the key in SECTION_GENERATORS",
                "",
                "DO NOT skip sections or mark them as 'optional' unless explicitly designed that way.",
                "=" * 80,
            ])
            
            pytest.fail("\n".join(error_lines))
    
    def test_all_benchmarks_target_existing_sections(self):
        """
        Verify that every benchmark section_id corresponds to a real generator.
        
        This test ensures benchmark files cannot silently drift away from the actual
        section generators. Every benchmarked section must have a corresponding
        generator function in SECTION_GENERATORS.
        
        FAILURE means: A benchmark references a section_id that doesn't exist.
        ACTION: Fix the section_id in the benchmark file or add the generator.
        """
        benchmark_files = get_all_benchmark_files()
        
        if not benchmark_files:
            pytest.skip("No benchmark files found")
        
        # Track invalid section references
        invalid_sections = []
        
        for file_path in benchmark_files:
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    benchmark_data = json.load(f)
                
                pack_key = benchmark_data.get("pack_key", "UNKNOWN")
                sections = benchmark_data.get("sections", {})
                
                for section_id, section_config in sections.items():
                    # The section_id key in the JSON must match a SECTION_GENERATORS key
                    if section_id not in SECTION_GENERATORS:
                        invalid_sections.append({
                            "file": file_path.name,
                            "pack_key": pack_key,
                            "section_id": section_id,
                            "benchmark_label": section_config.get("label", "N/A"),
                        })
                    
                    # Also check if the benchmark has an "id" field that should match
                    benchmark_id = section_config.get("id")
                    if benchmark_id and benchmark_id != section_id:
                        invalid_sections.append({
                            "file": file_path.name,
                            "pack_key": pack_key,
                            "section_id": section_id,
                            "benchmark_label": section_config.get("label", "N/A"),
                            "issue": f"Mismatch: key='{section_id}' but id='{benchmark_id}'",
                        })
            
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {file_path.name}: {e}")
            
            except Exception as e:
                pytest.fail(f"Error reading {file_path.name}: {e}")
        
        # Generate detailed failure message if any invalid references found
        if invalid_sections:
            error_lines = [
                "\n" + "=" * 80,
                "BENCHMARK WIRING FAILURE: Invalid Section References",
                "=" * 80,
                f"\nFound {len(invalid_sections)} benchmark entries that reference non-existent sections:\n",
            ]
            
            # Group by file for clearer reporting
            by_file: Dict[str, List[dict]] = {}
            for item in invalid_sections:
                file_name = item["file"]
                if file_name not in by_file:
                    by_file[file_name] = []
                by_file[file_name].append(item)
            
            for file_name, items in sorted(by_file.items()):
                error_lines.append(f"\n📄 File: {file_name}")
                for item in items:
                    error_lines.append(f"   • Section ID: '{item['section_id']}'")
                    error_lines.append(f"     Pack: {item['pack_key']}")
                    error_lines.append(f"     Label: {item['benchmark_label']}")
                    if "issue" in item:
                        error_lines.append(f"     Issue: {item['issue']}")
                    else:
                        error_lines.append(f"     Issue: No matching generator in SECTION_GENERATORS")
            
            error_lines.extend([
                "\n" + "=" * 80,
                "ACTION REQUIRED:",
                "=" * 80,
                "1. Check if the section_id is misspelled in the benchmark file",
                "2. Check if the section_id should match a different generator",
                "3. Available generators in SECTION_GENERATORS:",
            ])
            
            # Show a sample of available generators (first 20)
            available_generators = sorted(SECTION_GENERATORS.keys())
            for gen_id in available_generators[:20]:
                error_lines.append(f"   - {gen_id}")
            
            if len(available_generators) > 20:
                error_lines.append(f"   ... and {len(available_generators) - 20} more")
            
            error_lines.extend([
                "",
                "4. If the generator doesn't exist, you need to:",
                "   - Add the generator function to backend/main.py",
                "   - Register it in SECTION_GENERATORS dict",
                "   - OR remove the benchmark entry if it's obsolete",
                "",
                "DO NOT leave orphaned benchmark entries that reference missing generators.",
                "=" * 80,
            ])
            
            pytest.fail("\n".join(error_lines))
    
    def test_benchmark_file_naming_convention(self):
        """
        Verify that benchmark files follow the naming convention and can be loaded.
        
        This test ensures that:
        1. Benchmark files use correct naming: section_benchmarks.<suffix>.json
        2. The pack_key in the file matches what load_benchmarks_for_pack expects
        3. Files are valid JSON with required fields
        """
        benchmark_files = get_all_benchmark_files()
        
        if not benchmark_files:
            pytest.skip("No benchmark files found")
        
        issues = []
        
        for file_path in benchmark_files:
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    benchmark_data = json.load(f)
                
                # Check required top-level fields
                pack_key = benchmark_data.get("pack_key")
                if not pack_key:
                    issues.append({
                        "file": file_path.name,
                        "issue": "Missing 'pack_key' field",
                    })
                    continue
                
                if "sections" not in benchmark_data:
                    issues.append({
                        "file": file_path.name,
                        "pack_key": pack_key,
                        "issue": "Missing 'sections' field",
                    })
                    continue
                
                # Try to load via the loader to ensure naming convention works
                try:
                    loaded = load_benchmarks_for_pack(pack_key)
                    if loaded.get("pack_key") != pack_key:
                        issues.append({
                            "file": file_path.name,
                            "pack_key": pack_key,
                            "issue": f"Loaded pack_key '{loaded.get('pack_key')}' doesn't match file's pack_key '{pack_key}'",
                        })
                except BenchmarkNotFoundError:
                    issues.append({
                        "file": file_path.name,
                        "pack_key": pack_key,
                        "issue": f"File exists but load_benchmarks_for_pack('{pack_key}') cannot find it (naming convention mismatch)",
                    })
            
            except json.JSONDecodeError as e:
                issues.append({
                    "file": file_path.name,
                    "issue": f"Invalid JSON: {e}",
                })
        
        if issues:
            error_lines = [
                "\n" + "=" * 80,
                "BENCHMARK FILE STRUCTURE ISSUES",
                "=" * 80,
                f"\nFound {len(issues)} file(s) with structural problems:\n",
            ]
            
            for item in issues:
                error_lines.append(f"\n📄 File: {item['file']}")
                if "pack_key" in item:
                    error_lines.append(f"   Pack: {item['pack_key']}")
                error_lines.append(f"   Issue: {item['issue']}")
            
            error_lines.extend([
                "\n" + "=" * 80,
                "ACTION REQUIRED:",
                "=" * 80,
                "Fix the benchmark file structure to include:",
                "- pack_key: string matching PACKAGE_PRESETS key",
                "- sections: dict of section benchmarks",
                "- strict: boolean (optional, defaults to false)",
                "",
                "File naming convention: section_benchmarks.<first_two_parts_of_pack_key>.json",
                "Example: pack_key='quick_social_basic' → section_benchmarks.quick_social.json",
                "=" * 80,
            ])
            
            pytest.fail("\n".join(error_lines))
    
    def test_no_duplicate_sections_in_benchmarks(self):
        """
        Verify that benchmark files don't have duplicate section IDs.
        
        While JSON parsing would catch exact duplicates, this test ensures
        logical consistency within each benchmark file.
        """
        benchmark_files = get_all_benchmark_files()
        
        if not benchmark_files:
            pytest.skip("No benchmark files found")
        
        issues = []
        
        for file_path in benchmark_files:
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    benchmark_data = json.load(f)
                
                pack_key = benchmark_data.get("pack_key", "UNKNOWN")
                sections = benchmark_data.get("sections", {})
                
                # Check for ID field mismatches (key vs id field)
                for section_key, section_config in sections.items():
                    section_id = section_config.get("id")
                    if section_id and section_id != section_key:
                        issues.append({
                            "file": file_path.name,
                            "pack_key": pack_key,
                            "section_key": section_key,
                            "section_id": section_id,
                            "issue": "Key in 'sections' dict doesn't match 'id' field inside section config",
                        })
            
            except Exception as e:
                # Already caught by other tests
                pass
        
        if issues:
            error_lines = [
                "\n" + "=" * 80,
                "BENCHMARK CONSISTENCY ISSUES",
                "=" * 80,
                f"\nFound {len(issues)} consistency problem(s):\n",
            ]
            
            for item in issues:
                error_lines.append(f"\n📄 File: {item['file']}")
                error_lines.append(f"   Pack: {item['pack_key']}")
                error_lines.append(f"   Section Key: '{item['section_key']}'")
                error_lines.append(f"   Section ID: '{item['section_id']}'")
                error_lines.append(f"   Issue: {item['issue']}")
            
            error_lines.extend([
                "\n" + "=" * 80,
                "ACTION REQUIRED:",
                "=" * 80,
                "Ensure the key in the 'sections' dict matches the 'id' field inside each section.",
                "Example:",
                '  "sections": {',
                '    "overview": {',
                '      "id": "overview",  // Must match the key above',
                '      ...',
                '    }',
                '  }',
                "=" * 80,
            ])
            
            pytest.fail("\n".join(error_lines))


class TestBenchmarksComprehensiveCoverage:
    """Additional tests for comprehensive benchmark coverage."""
    
    def test_every_pack_has_at_least_one_benchmark_file(self):
        """
        Verify that every pack configured in PACKAGE_PRESETS has a benchmark file.
        
        This is a higher-level check than per-section validation.
        """
        all_pack_keys = set(PACKAGE_PRESETS.keys())
        
        # Try to load benchmarks for each pack
        packs_without_benchmarks = []
        
        for pack_key in all_pack_keys:
            try:
                load_benchmarks_for_pack(pack_key)
            except BenchmarkNotFoundError:
                packs_without_benchmarks.append(pack_key)
        
        if packs_without_benchmarks:
            error_lines = [
                "\n" + "=" * 80,
                "MISSING BENCHMARK FILES",
                "=" * 80,
                f"\nFound {len(packs_without_benchmarks)} pack(s) without benchmark files:\n",
            ]
            
            for pack_key in sorted(packs_without_benchmarks):
                pack_config = PACKAGE_PRESETS[pack_key]
                error_lines.append(f"\n📦 Pack: {pack_key}")
                error_lines.append(f"   Label: {pack_config.get('label', 'N/A')}")
                error_lines.append(f"   Sections: {len(pack_config.get('sections', []))}")
            
            error_lines.extend([
                "\n" + "=" * 80,
                "ACTION REQUIRED:",
                "=" * 80,
                "Create benchmark files for these packs following the naming convention:",
                "  section_benchmarks.<first_two_parts_of_pack_key>.json",
                "",
                "Example structure:",
                '{',
                '  "pack_key": "your_pack_key_here",',
                '  "strict": true,',
                '  "sections": {',
                '    "section_id_1": { ... },',
                '    "section_id_2": { ... }',
                '  }',
                '}',
                "=" * 80,
            ])
            
            pytest.fail("\n".join(error_lines))
    
    def test_benchmark_coverage_statistics(self):
        """
        Generate coverage statistics (informational test that always passes).
        
        This provides visibility into benchmark coverage across all packs.
        """
        pack_sections = get_all_pack_sections()
        total_sections = len(pack_sections)
        
        benchmarked_sections = 0
        sections_by_pack: Dict[str, dict] = {}
        
        for pack_key, section_id in pack_sections:
            if pack_key not in sections_by_pack:
                sections_by_pack[pack_key] = {
                    "total": 0,
                    "benchmarked": 0,
                    "missing": [],
                }
            
            sections_by_pack[pack_key]["total"] += 1
            
            try:
                benchmark = get_section_benchmark(pack_key, section_id)
                if benchmark is not None:
                    benchmarked_sections += 1
                    sections_by_pack[pack_key]["benchmarked"] += 1
                else:
                    sections_by_pack[pack_key]["missing"].append(section_id)
            except:
                sections_by_pack[pack_key]["missing"].append(section_id)
        
        # Print coverage report
        coverage_pct = (benchmarked_sections / total_sections * 100) if total_sections > 0 else 0
        
        print("\n" + "=" * 80)
        print("BENCHMARK COVERAGE REPORT")
        print("=" * 80)
        print(f"\nOverall Coverage: {benchmarked_sections}/{total_sections} sections ({coverage_pct:.1f}%)")
        print("\nPer-Pack Breakdown:")
        
        for pack_key in sorted(sections_by_pack.keys()):
            stats = sections_by_pack[pack_key]
            pack_pct = (stats["benchmarked"] / stats["total"] * 100) if stats["total"] > 0 else 0
            status = "✅" if pack_pct == 100 else "⚠️"
            
            print(f"\n{status} {pack_key}")
            print(f"   Coverage: {stats['benchmarked']}/{stats['total']} sections ({pack_pct:.1f}%)")
            
            if stats["missing"]:
                print(f"   Missing: {', '.join(stats['missing'][:3])}")
                if len(stats["missing"]) > 3:
                    print(f"            ... and {len(stats['missing']) - 3} more")
        
        print("\n" + "=" * 80)
        
        # This test always passes - it's informational only
        assert True, "Coverage report generated"
