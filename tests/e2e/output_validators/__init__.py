"""Output validators for client-facing artifacts."""

from .base import BaseValidator
from .pdf_validator import PDFValidator
from .pptx_validator import PPTXValidator
from .docx_validator import DOCXValidator
from .csv_validator import CSVValidator
from .zip_validator import ZIPValidator
from .html_validator import HTMLValidator


def get_validator(format_type: str) -> BaseValidator:
    """Get validator instance for a format type."""
    validators = {
        'pdf': PDFValidator(),
        'pptx': PPTXValidator(),
        'docx': DOCXValidator(),
        'csv': CSVValidator(),
        'zip': ZIPValidator(),
        'html': HTMLValidator(),
        'txt': HTMLValidator(),  # Reuse for plain text
    }
    
    if format_type not in validators:
        raise ValueError(f"No validator available for format: {format_type}")
    
    return validators[format_type]


__all__ = [
    'BaseValidator',
    'PDFValidator',
    'PPTXValidator',
    'DOCXValidator',
    'CSVValidator',
    'ZIPValidator',
    'HTMLValidator',
    'get_validator',
]
