#!/usr/bin/env python3
"""Validate E2E contract JSON schema."""
import json
import sys
from pathlib import Path

def check_contract():
    contract_path = Path('tests/e2e/specs/client_outputs.contract.json')
    
    if not contract_path.exists():
        print(f"FAIL: Contract file not found: {contract_path}")
        return False
    
    try:
        with open(contract_path) as f:
            contract = json.load(f)
    except json.JSONDecodeError as e:
        print(f"FAIL: Invalid JSON: {e}")
        return False
    
    # Check schema_version
    if 'schema_version' not in contract:
        print("FAIL: Missing 'schema_version' in contract")
        return False
    
    # Check outputs array
    if 'outputs' not in contract:
        print("FAIL: Missing 'outputs' array in contract")
        return False
    
    outputs = contract['outputs']
    if not isinstance(outputs, list):
        print("FAIL: 'outputs' is not a list")
        return False
    
    print(f"Contract schema_version: {contract['schema_version']}")
    print(f"Total outputs: {len(outputs)}")
    print("\nOutput IDs:")
    
    required_fields = ['id', 'format', 'required_sections']
    
    for i, output in enumerate(outputs, 1):
        if not isinstance(output, dict):
            print(f"FAIL: Output {i} is not a dict")
            return False
        
        # Check required fields
        for field in required_fields:
            if field not in output:
                print(f"FAIL: Output {i} missing '{field}'")
                return False
        
        print(f"  {i}. {output['id']} ({output['format']})")
    
    print("\nPASS: Contract is valid")
    return True

if __name__ == '__main__':
    success = check_contract()
    sys.exit(0 if success else 1)
