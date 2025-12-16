"""PDF validator."""

import os
from typing import Dict, Any
from .base import BaseValidator


class PDFValidator(BaseValidator):
    """Validates PDF documents."""
    
    def validate_structure(self, filepath: str, contract: Dict) -> Dict[str, Any]:
        """Validate PDF structure."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check file exists and is readable
        if not os.path.exists(filepath):
            result['valid'] = False
            result['errors'].append(f"PDF file not found: {filepath}")
            return result
        
        try:
            import PyPDF2
            
            with open(filepath, 'rb') as f:
                try:
                    reader = PyPDF2.PdfReader(f)
                    
                    # Check page count
                    page_count = len(reader.pages)
                    min_pages = contract.get('min_pages', 0)
                    max_pages = contract.get('max_pages', 9999)
                    
                    if page_count < min_pages:
                        result['valid'] = False
                        result['errors'].append(
                            f"Page count {page_count} < minimum {min_pages}"
                        )
                    
                    if page_count > max_pages:
                        result['valid'] = False
                        result['errors'].append(
                            f"Page count {page_count} > maximum {max_pages}"
                        )
                    
                    # Check metadata
                    required_metadata = contract.get('required_metadata', {})
                    metadata = reader.metadata or {}
                    
                    for key, required in required_metadata.items():
                        if required:
                            metadata_key = f'/{key.capitalize()}'
                            if metadata_key not in metadata:
                                result['warnings'].append(
                                    f"PDF metadata missing: {key}"
                                )
                    
                    result['page_count'] = page_count
                    result['metadata_present'] = len(metadata) > 0
                    
                except PyPDF2.errors.PdfReadError as e:
                    result['valid'] = False
                    result['errors'].append(f"PDF read error: {str(e)}")
                    
        except ImportError:
            result['warnings'].append("PyPDF2 not installed, skipping PDF validation")
        
        return result
    
    def validate_safety(self, filepath: str, contract: Dict) -> Dict[str, Any]:
        """Validate PDF safety."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Extract text for content validation
        text = self.extract_text(filepath)
        
        if not text:
            result['warnings'].append("No text extracted from PDF")
            return result
        
        # Check placeholders
        placeholder_valid, placeholder_issues = self.validate_placeholders(text, contract)
        if not placeholder_valid:
            result['valid'] = False
            result['errors'].extend(placeholder_issues)
        
        # Check required strings
        required_valid, required_issues = self.validate_required_strings(text, contract)
        if not required_valid:
            result['valid'] = False
            result['errors'].extend(required_issues)
        
        # Check file size
        size_valid, size_issues = self.validate_file_size(filepath, contract)
        if not size_valid:
            result['valid'] = False
            result['errors'].extend(size_issues)
        
        result['no_placeholders'] = placeholder_valid
        result['no_forbidden_phrases'] = placeholder_valid
        result['required_strings_present'] = required_valid
        
        return result
    
    def extract_text(self, filepath: str) -> str:
        """Extract text from PDF."""
        try:
            import PyPDF2
            
            text_parts = []
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text_parts.append(page.extract_text())
            
            return '\n'.join(text_parts)
        except (ImportError, Exception):
            return ""
