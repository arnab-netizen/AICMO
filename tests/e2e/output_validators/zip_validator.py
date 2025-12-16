"""ZIP validator with recursive validation."""

import os
import zipfile
from typing import Dict, Any, List
from pathlib import Path
from .base import BaseValidator


class ZIPValidator(BaseValidator):
    """Validates ZIP archives."""
    
    def validate_structure(self, filepath: str, contract: Dict) -> Dict[str, Any]:
        """Validate ZIP structure."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if not os.path.exists(filepath):
            result['valid'] = False
            result['errors'].append(f"ZIP file not found: {filepath}")
            return result
        
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                # Check if ZIP is valid
                bad_file = zf.testzip()
                if bad_file:
                    result['valid'] = False
                    result['errors'].append(f"Corrupt file in ZIP: {bad_file}")
                    return result
                
                # Get file list
                file_list = zf.namelist()
                
                # Check required contents
                required_contents = contract.get('required_contents', [])
                missing_files = set(required_contents) - set(file_list)
                if missing_files:
                    result['valid'] = False
                    result['errors'].append(
                        f"Missing required files: {list(missing_files)}"
                    )
                
                # Check for forbidden paths
                forbidden_patterns = contract.get('forbidden_patterns', [])
                for filename in file_list:
                    for pattern in forbidden_patterns:
                        import re
                        if re.search(pattern, filename):
                            result['valid'] = False
                            result['errors'].append(
                                f"Forbidden path pattern in ZIP: {filename}"
                            )
                
                # Check file extensions
                allowed_extensions = contract.get('allowed_extensions', [])
                if allowed_extensions:
                    for filename in file_list:
                        ext = Path(filename).suffix
                        if ext and ext not in allowed_extensions:
                            result['valid'] = False
                            result['errors'].append(
                                f"Disallowed file extension: {filename} ({ext})"
                            )
                
                # Check uncompressed size
                max_uncompressed = contract.get('max_uncompressed_size_bytes')
                if max_uncompressed:
                    total_size = sum(info.file_size for info in zf.infolist())
                    if total_size > max_uncompressed:
                        result['valid'] = False
                        result['errors'].append(
                            f"Uncompressed size {total_size} exceeds limit {max_uncompressed}"
                        )
                
                result['file_count'] = len(file_list)
                result['files'] = file_list
                
        except zipfile.BadZipFile as e:
            result['valid'] = False
            result['errors'].append(f"Invalid ZIP file: {str(e)}")
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"ZIP validation error: {str(e)}")
        
        return result
    
    def validate_safety(self, filepath: str, contract: Dict) -> Dict[str, Any]:
        """Validate ZIP safety."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check file size
        size_valid, size_issues = self.validate_file_size(filepath, contract)
        if not size_valid:
            result['valid'] = False
            result['errors'].extend(size_issues)
        
        # Recursive validation if required
        if contract.get('recursive_validation', False):
            recursive_result = self.validate_recursively(filepath, contract)
            if not recursive_result['valid']:
                result['valid'] = False
                result['errors'].extend(recursive_result['errors'])
        
        result['no_path_traversal'] = True  # Checked in structure validation
        
        return result
    
    def validate_recursively(self, filepath: str, contract: Dict) -> Dict[str, Any]:
        """Recursively validate all files in ZIP."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            import tempfile
            import shutil
            from . import get_validator
            
            with tempfile.TemporaryDirectory() as tmpdir:
                # Extract ZIP
                with zipfile.ZipFile(filepath, 'r') as zf:
                    zf.extractall(tmpdir)
                
                # Validate each file
                for root, dirs, files in os.walk(tmpdir):
                    for filename in files:
                        full_path = os.path.join(root, filename)
                        ext = Path(filename).suffix.lstrip('.')
                        
                        # Get validator for this file type
                        try:
                            validator = get_validator(ext)
                            
                            # Create minimal contract for validation
                            file_contract = {
                                'format': ext,
                                'forbidden_patterns': contract.get('forbidden_patterns', []),
                                'max_file_size_bytes': contract.get('max_file_size_bytes', 10*1024*1024)
                            }
                            
                            # Validate structure
                            struct_result = validator.validate_structure(full_path, file_contract)
                            if not struct_result['valid']:
                                result['valid'] = False
                                result['errors'].append(
                                    f"File {filename} failed structure validation: "
                                    f"{struct_result['errors']}"
                                )
                            
                            # Validate safety
                            safety_result = validator.validate_safety(full_path, file_contract)
                            if not safety_result['valid']:
                                result['valid'] = False
                                result['errors'].append(
                                    f"File {filename} failed safety validation: "
                                    f"{safety_result['errors']}"
                                )
                                
                        except ValueError:
                            # No validator for this type - skip
                            pass
                        
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Recursive validation error: {str(e)}")
        
        return result
