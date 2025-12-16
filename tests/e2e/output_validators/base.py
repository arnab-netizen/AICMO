"""Base validator interface for output validation."""

import re
from abc import ABC, abstractmethod
from typing import Dict, List, Any


class BaseValidator(ABC):
    """Base class for output validators."""
    
    @abstractmethod
    def validate_structure(self, filepath: str, contract: Dict) -> Dict[str, Any]:
        """
        Validate structural integrity of the output.
        
        Returns:
            Dict with 'valid' (bool), 'errors' (list), 'warnings' (list)
        """
        pass
    
    @abstractmethod
    def validate_safety(self, filepath: str, contract: Dict) -> Dict[str, Any]:
        """
        Validate safety aspects (no placeholders, forbidden phrases, etc.).
        
        Returns:
            Dict with 'valid' (bool), 'errors' (list), 'warnings' (list)
        """
        pass
    
    def extract_text(self, filepath: str) -> str:
        """
        Extract text content from file for validation.
        Subclasses should implement format-specific extraction.
        
        Returns:
            Extracted text content
        """
        return ""
    
    def validate_placeholders(self, text: str, contract: Dict) -> tuple[bool, List[str]]:
        """
        Check for forbidden placeholder patterns.
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        forbidden_patterns = contract.get('forbidden_patterns', [])
        dynamic_allowlist = contract.get('dynamic_allowlist_patterns', [])
        
        for pattern in forbidden_patterns:
            # Skip allowlisted patterns
            if pattern in dynamic_allowlist:
                continue
            
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Limit matches shown to first 3
                    sample_matches = matches[:3]
                    issues.append(
                        f"Forbidden pattern '{pattern}' found: {sample_matches}"
                    )
            except re.error as e:
                issues.append(f"Invalid regex pattern '{pattern}': {e}")
        
        return len(issues) == 0, issues
    
    def validate_required_strings(self, text: str, contract: Dict) -> tuple[bool, List[str]]:
        """
        Check for required strings (non-template).
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        required_strings = contract.get('required_strings', [])
        dynamic_allowlist = contract.get('dynamic_allowlist_patterns', [])
        
        for required in required_strings:
            # Skip template variables (they'll be substituted at runtime)
            if required in dynamic_allowlist:
                continue
            
            # Check for exact match
            if required not in text:
                issues.append(f"Required string not found: '{required}'")
        
        return len(issues) == 0, issues
    
    def validate_file_size(self, filepath: str, contract: Dict) -> tuple[bool, List[str]]:
        """
        Validate file size is within limits.
        
        Returns:
            (is_valid, list_of_issues)
        """
        import os
        
        issues = []
        max_size = contract.get('max_file_size_bytes')
        
        if max_size is not None:
            actual_size = os.path.getsize(filepath)
            if actual_size > max_size:
                issues.append(
                    f"File size {actual_size} bytes exceeds maximum {max_size} bytes"
                )
        
        return len(issues) == 0, issues
