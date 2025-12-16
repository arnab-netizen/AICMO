#!/usr/bin/env python3
"""Test if validators can be imported and instantiated."""
import sys
from pathlib import Path

# Add tests/e2e to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'tests' / 'e2e'))

def test_validators():
    try:
        from output_validators import get_validator
        
        print("Testing validator factory...")
        
        # Test each validator type
        formats = ['pdf', 'pptx', 'docx', 'csv', 'zip', 'html']
        
        for fmt in formats:
            validator = get_validator(fmt)
            print(f"  ✓ {fmt.upper()} validator: {validator.__class__.__name__}")
        
        print("\nPASS: All validators can be instantiated")
        return True
        
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_validators()
    sys.exit(0 if success else 1)
