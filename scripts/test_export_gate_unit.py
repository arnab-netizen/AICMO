"""
Unit test for export gate - Phase A.1 proof with PASS and FAIL cases.

Tests contract resolution and validation with:
- PASS case: valid output meets contract
- FAIL case: controlled violation (not "no contract")
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Set up environment for E2E mode
os.environ["AICMO_E2E_MODE"] = "1"
os.environ["AICMO_TEST_SEED"] = "unit_test_12345"

# Create temp artifact directory
TEMP_ARTIFACT_DIR = tempfile.mkdtemp(prefix="aicmo_unit_test_")
os.environ["AICMO_E2E_ARTIFACT_DIR"] = TEMP_ARTIFACT_DIR

print(f"Using temp artifact dir: {TEMP_ARTIFACT_DIR}")

# Import after setting env vars
from aicmo.validation.export_gate import process_export_with_gate, reset_export_gate
from aicmo.validation import get_runtime_paths, reset_runtime_paths
from aicmo.delivery.gate import DeliveryBlockedError

# Mock PDF content (minimal valid PDF)
MOCK_PDF = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(AICMO Test Report) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF
"""

# Mock structured output - VALID (meets min word count)
MOCK_VALID_OUTPUT = {
    "title": "AICMO Test Report",
    "sections": {
        "Executive Summary": "This is a comprehensive executive summary with sufficient word count to pass validation requirements. " * 10,
        "Market Analysis": "Market analysis content with detailed insights and recommendations for strategic planning. " * 10,
        "Marketing Strategy": "Strategic recommendations and tactical implementation plans for execution. " * 10,
    },
    "metadata": {
        "client_name": "Unit Test Client",
        "generated_at": "2025-12-15T13:00:00Z",
        "format": "pdf",
    },
}

# Mock structured output - VIOLATION (includes forbidden TODO in section title)
MOCK_VIOLATION_OUTPUT = {
    "title": "AICMO Test Report",
    "sections": {
        "Executive Summary": "This is a test executive summary with sufficient content for validation. " * 10,
        "TODO: Market Analysis": "Market analysis content that would otherwise be valid. " * 10,
    },
    "metadata": {
        "client_name": "Unit Test Client",
        "generated_at": "2025-12-15T13:00:00Z",
        "format": "pdf",
    },
}


def test_pass_case():
    """Test 1: PASS case - valid output meets contract."""
    print("\n" + "="*80)
    print("TEST 1: PASS CASE - Valid Output")
    print("="*80 + "\n")
    
    # Reset for clean run with unique seed
    reset_export_gate()
    reset_runtime_paths()
    os.environ["AICMO_TEST_SEED"] = "unit_test_pass_12345"
    
    mock_brief = {
        "brand": {
            "brand_name": "Unit Test Client",
            "industry": "Technology",
        },
        "objective": "Test E2E gate with PASS",
    }
    
    try:
        # Call export gate with valid output
        print("1. Calling process_export_with_gate() with valid output...")
        result_bytes, validation_report = process_export_with_gate(
            brief=mock_brief,
            output=MOCK_VALID_OUTPUT,
            file_bytes=MOCK_PDF,
            format_="pdf",
            filename="test_report_pass.pdf",
        )
        
        print("   ✓ Export gate processed successfully")
        print(f"   ✓ Returned {len(result_bytes)} bytes")
        print(f"   ✓ Validation report status: {validation_report.get('global_status', 'UNKNOWN')}")
        
        # Get runtime paths
        paths = get_runtime_paths()
        print(f"\n2. Run directory: {paths.run_dir}")
        
        # Check artifacts
        print("\n3. Checking generated artifacts...")
        
        manifest_path = paths.manifest_path
        validation_path = paths.validation_path
        section_map_path = paths.section_map_path
        downloads_dir = paths.downloads_dir
        
        assert manifest_path.exists(), f"Manifest not found: {manifest_path}"
        print("   ✓ Manifest found")
        
        assert validation_path.exists(), f"Validation report not found: {validation_path}"
        print("   ✓ Validation report found")
        
        assert section_map_path.exists(), f"Section map not found: {section_map_path}"
        print("   ✓ Section map found")
        
        assert downloads_dir.exists(), f"Downloads dir not found: {downloads_dir}"
        download_files = list(downloads_dir.glob("*"))
        assert len(download_files) > 0, "No download files found"
        print(f"   ✓ Download files found: {[f.name for f in download_files]}")
        
        # Load and check validation report
        with open(validation_path, 'r') as f:
            validation_data = json.load(f)
        
        print(f"\n4. Validation Report:")
        print(f"   Global Status: {validation_data.get('global_status', 'UNKNOWN')}")
        
        # Check for PASS or explicit reason
        if validation_data.get('global_status') == 'PASS':
            print("   ✅ VALIDATION PASSED")
        else:
            print(f"   ⚠️  Status: {validation_data.get('global_status')}")
            if validation_data.get('artifacts'):
                for artifact in validation_data['artifacts']:
                    if artifact.get('issues'):
                        print(f"   Issues in {artifact['artifact_id']}:")
                        for issue in artifact['issues']:
                            print(f"     - {issue}")
        
        # Load and check manifest - verify output_id
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
        
        print(f"\n5. Manifest:")
        assert 'artifacts' in manifest_data, "Manifest missing 'artifacts' field"
        assert len(manifest_data['artifacts']) > 0, "Manifest has no artifacts"
        
        artifact = manifest_data['artifacts'][0]
        assert 'artifact_id' in artifact, "Artifact missing 'artifact_id' field"
        print(f"   ✓ Output ID: {artifact['artifact_id']}")
        print(f"   ✓ Filename: {artifact.get('filename', 'unknown')}")
        print(f"   ✓ Checksum: {artifact.get('checksum_sha256', 'unknown')[:16]}...")
        
        # Check section map
        with open(section_map_path, 'r') as f:
            section_map_data = json.load(f)
        
        print(f"\n6. Section Map:")
        print(f"   Document ID: {section_map_data.get('document_id', 'unknown')}")
        print(f"   Sections: {len(section_map_data.get('sections', []))}")
        print(f"   Total words: {section_map_data.get('total_word_count', 0)}")
        
        print("\n" + "="*80)
        print("✅ TEST 1 PASSED: Valid output processed successfully")
        print("="*80)
        
        return True, paths.run_dir
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_fail_case():
    """Test 2: FAIL case - controlled violation (not 'no contract')."""
    print("\n" + "="*80)
    print("TEST 2: FAIL CASE - Controlled Violation")
    print("="*80 + "\n")
    
    # Reset for clean run with unique seed
    reset_export_gate()
    reset_runtime_paths()
    os.environ["AICMO_TEST_SEED"] = "unit_test_fail_67890"
    
    mock_brief = {
        "brand": {
            "brand_name": "Unit Test Client",
            "industry": "Technology",
        },
        "objective": "Test E2E gate with FAIL",
    }
    
    try:
        # Call export gate with violation output (TODO in section title)
        print("1. Calling process_export_with_gate() with TODO in section title...")
        result_bytes, validation_report = process_export_with_gate(
            brief=mock_brief,
            output=MOCK_VIOLATION_OUTPUT,
            file_bytes=MOCK_PDF,
            format_="pdf",
            filename="test_report_fail.pdf",
        )
        
        print(f"   Validation status: {validation_report.get('global_status', 'UNKNOWN')}")
        
        # Get paths
        paths = get_runtime_paths()
        
        # Check validation report
        validation_path = paths.validation_path
        if validation_path.exists():
            with open(validation_path, 'r') as f:
                validation_data = json.load(f)
            
            print(f"\n2. Validation Report:")
            print(f"   Global Status: {validation_data.get('global_status', 'UNKNOWN')}")
            
            if validation_data.get('global_status') == 'FAIL':
                print("   ✅ Validation correctly reported FAIL")
                
                # Check reason is NOT "no contract"
                issues = []
                for artifact in validation_data.get('artifacts', []):
                    issues.extend(artifact.get('issues', []))
                
                has_no_contract_error = any('No contract found' in issue for issue in issues)
                if has_no_contract_error:
                    print("   ❌ ERROR: Failure reason is 'no contract' - SHOULD BE VIOLATION")
                    return False, paths.run_dir
                else:
                    print("   ✅ Failure reason is specific violation (not 'no contract')")
                    for issue in issues[:3]:  # Show first 3
                        print(f"     - {issue}")
                    
                    print("\n" + "="*80)
                    print("✅ TEST 2 PASSED: Validation correctly detected forbidden pattern")
                    print("="*80)
                    return True, paths.run_dir
            else:
                print(f"   ❌ Status is not FAIL: {validation_data.get('global_status')}")
                print("   Expected FAIL due to TODO in section title")
                
                print("\n" + "="*80)
                print("❌ TEST 2 FAILED: Validation should have detected forbidden pattern")
                print("="*80)
                return False, paths.run_dir
        
        print("\n" + "="*80)
        print("❌ TEST 2 FAILED: Validation report not found")
        print("="*80)
        return False, paths.run_dir
        
    except DeliveryBlockedError as e:
        print(f"   ✅ Delivery BLOCKED with: {e}")
        
        # Get paths
        paths = get_runtime_paths()
        
        # Check that blocking reason is NOT "no contract"
        error_msg = str(e)
        if 'No contract found' in error_msg:
            print("   ❌ ERROR: Blocking reason is 'no contract' - SHOULD BE VIOLATION")
            return False, paths.run_dir
        
        print("   ✅ Blocking reason is specific violation (not 'no contract')")
        
        # Check artifacts still exist
        print(f"\n2. Run directory: {paths.run_dir}")
        
        validation_path = paths.validation_path
        if validation_path.exists():
            with open(validation_path, 'r') as f:
                validation_data = json.load(f)
            
            print(f"\n3. Validation Report:")
            print(f"   Global Status: {validation_data.get('global_status', 'UNKNOWN')}")
            
            # Show issues
            for artifact in validation_data.get('artifacts', []):
                if artifact.get('issues'):
                    print(f"   Issues in {artifact['artifact_id']}:")
                    for issue in artifact['issues'][:3]:
                        print(f"     - {issue}")
        
        print("\n" + "="*80)
        print("✅ TEST 2 PASSED: Delivery blocked for specific violation")
        print("="*80)
        
        return True, paths.run_dir
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def main():
    """Run both tests and report results."""
    print("\n" + "="*80)
    print("E2E GATE UNIT TEST - Phase A.1 Proof")
    print("Contract Resolution + Output ID Mapping")
    print("="*80)
    
    results = []
    run_dirs = []
    
    # Test 1: PASS case
    passed, run_dir = test_pass_case()
    results.append(("PASS Case", passed))
    if run_dir:
        run_dirs.append(("PASS", run_dir))
    
    # Test 2: FAIL case
    passed, run_dir = test_fail_case()
    results.append(("FAIL Case", passed))
    if run_dir:
        run_dirs.append(("FAIL", run_dir))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nArtifacts directory: {TEMP_ARTIFACT_DIR}")
    for label, run_dir in run_dirs:
        print(f"  {label} run: {run_dir}")
    
    # Ask before cleanup
    response = input("\nDelete temp directory? (y/N): ")
    if response.lower() == 'y':
        shutil.rmtree(TEMP_ARTIFACT_DIR, ignore_errors=True)
        print("✓ Cleaned up")
    else:
        print(f"✓ Artifacts preserved at: {TEMP_ARTIFACT_DIR}")
    
    # Exit code
    all_passed = all(passed for _, passed in results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
