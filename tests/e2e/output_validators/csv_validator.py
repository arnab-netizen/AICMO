"""CSV validator."""

import os
import csv
from typing import Dict, Any
from .base import BaseValidator


class CSVValidator(BaseValidator):
    """Validates CSV files."""
    
    def validate_structure(self, filepath: str, contract: Dict) -> Dict[str, Any]:
        """Validate CSV structure."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if not os.path.exists(filepath):
            result['valid'] = False
            result['errors'].append(f"CSV file not found: {filepath}")
            return result
        
        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Check required columns
                required_columns = contract.get('required_columns', [])
                actual_columns = reader.fieldnames or []
                
                missing_columns = set(required_columns) - set(actual_columns)
                if missing_columns:
                    result['valid'] = False
                    result['errors'].append(
                        f"Missing required columns: {list(missing_columns)}"
                    )
                
                # Check row count
                rows = list(reader)
                row_count = len(rows)
                min_rows = contract.get('min_rows', 0)
                max_rows = contract.get('max_rows', float('inf'))
                
                if row_count < min_rows:
                    result['valid'] = False
                    result['errors'].append(
                        f"Row count {row_count} < minimum {min_rows}"
                    )
                
                if row_count > max_rows:
                    result['valid'] = False
                    result['errors'].append(
                        f"Row count {row_count} > maximum {max_rows}"
                    )
                
                result['row_count'] = row_count
                result['column_count'] = len(actual_columns)
                result['columns'] = actual_columns
                
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"CSV read error: {str(e)}")
        
        return result
    
    def validate_safety(self, filepath: str, contract: Dict) -> Dict[str, Any]:
        """Validate CSV safety."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Extract text
        text = self.extract_text(filepath)
        
        # Check placeholders
        placeholder_valid, placeholder_issues = self.validate_placeholders(text, contract)
        if not placeholder_valid:
            result['valid'] = False
            result['errors'].extend(placeholder_issues)
        
        # Check file size
        size_valid, size_issues = self.validate_file_size(filepath, contract)
        if not size_valid:
            result['valid'] = False
            result['errors'].extend(size_issues)
        
        result['no_placeholders'] = placeholder_valid
        
        return result
    
    def extract_text(self, filepath: str) -> str:
        """Extract text from CSV."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""
