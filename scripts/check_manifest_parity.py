#!/usr/bin/env python3
"""
Manifest Parity Checker

Verifies that downloaded files in a run folder exactly match the artifacts
listed in the manifest JSON (single source of truth).

Usage:
    python scripts/check_manifest_parity.py [run_folder]
    
If no run_folder is provided, finds the latest run in AICMO_E2E_ARTIFACT_DIR.

Exit codes:
    0: PASS - All files match manifest
    1: FAIL - Parity check failed
    2: ERROR - Missing manifest or invalid structure
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

def find_latest_run(artifact_dir: str) -> Path:
    """Find the most recent run directory."""
    artifact_path = Path(artifact_dir)
    
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact directory not found: {artifact_dir}")
    
    # Find all run directories (format: run_*)
    run_dirs = [d for d in artifact_path.iterdir() if d.is_dir() and d.name.startswith('run_')]
    
    if not run_dirs:
        raise FileNotFoundError(f"No run directories found in {artifact_dir}")
    
    # Sort by modification time, most recent first
    run_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    
    return run_dirs[0]


def load_manifest(run_folder: Path) -> Dict:
    """Load manifest JSON from run folder."""
    manifest_path = run_folder / "manifest" / "client_output_manifest.json"
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        return json.load(f)


def check_parity(run_folder: Path, manifest: Dict) -> Tuple[bool, List[str], List[str]]:
    """
    Check parity between manifest and actual files.
    
    Returns:
        (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    # Get artifacts from manifest
    artifacts = manifest.get('artifacts', [])
    
    if not artifacts:
        errors.append("Manifest contains no artifacts")
        return False, errors, warnings
    
    print(f"\n📋 Manifest lists {len(artifacts)} artifact(s):")
    for artifact in artifacts:
        print(f"  - {artifact['filename']} ({artifact['artifact_id']})")
    
    # Check downloads directory
    downloads_dir = run_folder / "downloads"
    
    if not downloads_dir.exists():
        errors.append(f"Downloads directory not found: {downloads_dir}")
        return False, errors, warnings
    
    # Get actual files in downloads
    actual_files = set([f.name for f in downloads_dir.glob("*") if f.is_file()])
    
    print(f"\n📁 Downloads directory contains {len(actual_files)} file(s):")
    for filename in sorted(actual_files):
        print(f"  - {filename}")
    
    # Get expected files from manifest
    expected_files = set([artifact['filename'] for artifact in artifacts])
    
    # Check for missing files (in manifest but not in downloads)
    missing_files = expected_files - actual_files
    if missing_files:
        for filename in missing_files:
            errors.append(f"File in manifest but missing from downloads: {filename}")
    
    # Check for extra files (in downloads but not in manifest)
    extra_files = actual_files - expected_files
    if extra_files:
        for filename in extra_files:
            warnings.append(f"File in downloads but not in manifest: {filename}")
    
    # Verify file sizes and checksums
    print(f"\n🔍 Verifying file integrity:")
    for artifact in artifacts:
        filename = artifact['filename']
        file_path = downloads_dir / filename
        
        if not file_path.exists():
            continue  # Already reported as missing
        
        # Check file size
        actual_size = file_path.stat().st_size
        expected_size = artifact.get('size_bytes')
        
        if expected_size and actual_size != expected_size:
            errors.append(
                f"File size mismatch for {filename}: "
                f"expected {expected_size} bytes, got {actual_size} bytes"
            )
        else:
            print(f"  ✓ {filename}: size OK ({actual_size} bytes)")
        
        # Check checksum if available
        expected_checksum = artifact.get('checksum_sha256')
        if expected_checksum:
            import hashlib
            with open(file_path, 'rb') as f:
                actual_checksum = hashlib.sha256(f.read()).hexdigest()
            
            if actual_checksum != expected_checksum:
                errors.append(
                    f"Checksum mismatch for {filename}: "
                    f"expected {expected_checksum[:16]}..., got {actual_checksum[:16]}..."
                )
            else:
                print(f"  ✓ {filename}: checksum OK ({actual_checksum[:16]}...)")
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def main():
    """Main entry point."""
    # Get run folder from args or find latest
    if len(sys.argv) > 1:
        run_folder = Path(sys.argv[1])
    else:
        artifact_dir = os.getenv('AICMO_E2E_ARTIFACT_DIR', './.artifacts/e2e')
        try:
            run_folder = find_latest_run(artifact_dir)
            print(f"📂 Using latest run: {run_folder}")
        except FileNotFoundError as e:
            print(f"❌ ERROR: {e}", file=sys.stderr)
            return 2
    
    if not run_folder.exists():
        print(f"❌ ERROR: Run folder not found: {run_folder}", file=sys.stderr)
        return 2
    
    # Load manifest
    try:
        manifest = load_manifest(run_folder)
        print(f"✓ Loaded manifest: {run_folder / 'manifest' / 'client_output_manifest.json'}")
        print(f"  Run ID: {manifest.get('run_id')}")
        print(f"  Client ID: {manifest.get('client_id')}")
    except FileNotFoundError as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid manifest JSON: {e}", file=sys.stderr)
        return 2
    
    # Check parity
    is_valid, errors, warnings = check_parity(run_folder, manifest)
    
    # Print results
    print("\n" + "="*80)
    print("MANIFEST PARITY CHECK RESULTS")
    print("="*80)
    
    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")
    
    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
        print(f"\n{'='*80}")
        print("RESULT: FAIL")
        print("="*80)
        return 1
    else:
        print(f"\n✅ All checks passed!")
        print(f"  - All manifest artifacts present in downloads")
        print(f"  - File sizes match")
        print(f"  - Checksums valid")
        print(f"\n{'='*80}")
        print("RESULT: PASS")
        print("="*80)
        return 0


if __name__ == '__main__':
    sys.exit(main())
