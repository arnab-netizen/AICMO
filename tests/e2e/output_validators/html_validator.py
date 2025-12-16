"""HTML/Text validator."""

import os
from typing import Dict, Any
from .base import BaseValidator


class HTMLValidator(BaseValidator):
    """Validates HTML and plain text files."""
    
    def validate_structure(self, filepath: str, contract: Dict) -> Dict[str, Any]:
        """Validate HTML/text structure."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if not os.path.exists(filepath):
            result['valid'] = False
            result['errors'].append(f"File not found: {filepath}")
            return result
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check minimum character count
            min_chars = contract.get('min_character_count', 0)
            max_chars = contract.get('max_character_count', float('inf'))
            char_count = len(content)
            
            if char_count < min_chars:
                result['valid'] = False
                result['errors'].append(
                    f"Character count {char_count} < minimum {min_chars}"
                )
            
            if char_count > max_chars:
                result['valid'] = False
                result['errors'].append(
                    f"Character count {char_count} > maximum {max_chars}"
                )
            
            # If HTML, check for basic validity
            if filepath.endswith('.html'):
                try:
                    from html.parser import HTMLParser
                    
                    class HTMLValidationParser(HTMLParser):
                        def __init__(self):
                            super().__init__()
                            self.errors = []
                        
                        def error(self, message):
                            self.errors.append(message)
                    
                    parser = HTMLValidationParser()
                    parser.feed(content)
                    
                    if parser.errors:
                        result['warnings'].append(
                            f"HTML parsing issues: {parser.errors[:3]}"
                        )
                        
                except ImportError:
                    pass
            
            result['character_count'] = char_count
            result['has_content'] = char_count > 0
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"File read error: {str(e)}")
        
        return result
    
    def validate_safety(self, filepath: str, contract: Dict) -> Dict[str, Any]:
        """Validate HTML/text safety."""
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
        
        # Check required strings
        required_valid, required_issues = self.validate_required_strings(text, contract)
        if not required_valid:
            result['valid'] = False
            result['errors'].extend(required_issues)
        
        # Check required elements for HTML
        if filepath.endswith('.html'):
            required_elements = contract.get('required_elements', [])
            for element in required_elements:
                # Simple check - just see if element name appears
                if element not in text.lower():
                    result['warnings'].append(
                        f"Required element may be missing: {element}"
                    )
        
        # Check file size
        size_valid, size_issues = self.validate_file_size(filepath, contract)
        if not size_valid:
            result['valid'] = False
            result['errors'].extend(size_issues)
        
        result['no_placeholders'] = placeholder_valid
        result['required_strings_present'] = required_valid
        
        return result
    
    def extract_text(self, filepath: str) -> str:
        """Extract text from HTML/text file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""
