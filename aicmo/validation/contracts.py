"""
Canonical Contract Loader for E2E Client Output Validation.

Single source of truth for loading and resolving contracts.
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass


class ContractNotFoundError(Exception):
    """Raised when contract file or specific contract ID is not found."""
    pass


class ContractSchemaError(Exception):
    """Raised when contract JSON schema is invalid."""
    pass


class ContractViolationError(Exception):
    """Raised when output violates contract rules."""
    pass


class OutputIdMissingError(Exception):
    """Raised when artifact is missing required output_id."""
    pass


class MissingRuntimeVarError(Exception):
    """Raised when runtime variable is missing for substitution."""
    pass


@dataclass
class ContractSpec:
    """Normalized contract specification."""
    id: str
    schema_version: str
    format: str
    required_sections: List[str]
    required_strings: List[str]
    forbidden_patterns: List[str]
    min_word_count_total: int
    min_word_count_by_section: Dict[str, int]
    min_pages: Optional[int]
    max_pages: Optional[int]
    max_file_size_bytes: Optional[int]
    required_metadata: Dict
    raw_contract: Dict  # Original contract dict


def get_contract_path() -> Path:
    """
    Resolve contract path using resolution order:
    1. AICMO_CONTRACT_PATH env var if set
    2. Default repo path: tests/e2e/specs/client_outputs.contract.json
    
    Returns:
        Path to contract file
        
    Raises:
        ContractNotFoundError: If file doesn't exist
    """
    # Try env var first
    env_path = os.getenv('AICMO_CONTRACT_PATH')
    if env_path:
        contract_path = Path(env_path)
        if not contract_path.exists():
            raise ContractNotFoundError(
                f"Contract path from AICMO_CONTRACT_PATH not found: {contract_path}"
            )
        return contract_path
    
    # Default repo path
    repo_root = Path(__file__).parent.parent.parent
    default_path = repo_root / 'tests' / 'e2e' / 'specs' / 'client_outputs.contract.json'
    
    if not default_path.exists():
        raise ContractNotFoundError(
            f"Default contract path not found: {default_path}\n"
            f"Set AICMO_CONTRACT_PATH env var to specify alternative location."
        )
    
    return default_path


def load_contracts(contract_path: Optional[str] = None) -> Dict:
    """
    Load contracts from JSON file.
    
    Args:
        contract_path: Optional explicit path. If None, uses resolution order.
        
    Returns:
        Dict with structure: {
            'schema_version': str,
            'outputs': List[Dict]
        }
        
    Raises:
        ContractNotFoundError: If file doesn't exist
        ContractSchemaError: If JSON schema is invalid
    """
    if contract_path:
        path = Path(contract_path)
        if not path.exists():
            raise ContractNotFoundError(f"Contract file not found: {path}")
    else:
        path = get_contract_path()
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ContractSchemaError(f"Invalid JSON in contract file: {e}")
    
    # Validate top-level schema
    if not isinstance(data, dict):
        raise ContractSchemaError("Contract must be a JSON object (dict)")
    
    # Normalize schema_version field (accept schemaVersion or schema_version)
    if 'schema_version' not in data and 'schemaVersion' in data:
        data['schema_version'] = data['schemaVersion']
    
    if 'schema_version' not in data:
        raise ContractSchemaError("Missing required field: 'schema_version'")
    
    if 'outputs' not in data:
        raise ContractSchemaError("Missing required field: 'outputs'")
    
    if not isinstance(data['outputs'], list):
        raise ContractSchemaError("Field 'outputs' must be a list")
    
    # Validate each output contract
    for idx, output in enumerate(data['outputs']):
        if not isinstance(output, dict):
            raise ContractSchemaError(f"Output #{idx} must be a dict")
        
        required_fields = ['id', 'format', 'schema_version']
        for field in required_fields:
            if field not in output:
                raise ContractSchemaError(
                    f"Output #{idx} missing required field: '{field}'"
                )
    
    return data


def normalize_contract(raw: Dict) -> ContractSpec:
    """
    Normalize raw contract dict to ContractSpec.
    
    Args:
        raw: Raw contract dict from JSON
        
    Returns:
        Normalized ContractSpec
    """
    return ContractSpec(
        id=raw['id'],
        schema_version=raw['schema_version'],
        format=raw['format'],
        required_sections=raw.get('required_sections', []),
        required_strings=raw.get('required_strings', []),
        forbidden_patterns=raw.get('forbidden_patterns', []),
        min_word_count_total=raw.get('min_word_count_total', 0),
        min_word_count_by_section=raw.get('min_word_count_by_section', {}),
        min_pages=raw.get('min_pages'),
        max_pages=raw.get('max_pages'),
        max_file_size_bytes=raw.get('max_file_size_bytes'),
        required_metadata=raw.get('required_metadata', {}),
        raw_contract=raw,
    )


def get_contract_for_output(output_id: str, contracts: Dict) -> ContractSpec:
    """
    Get contract for specific output_id.
    
    Args:
        output_id: Output identifier (must match contract 'id' field)
        contracts: Loaded contracts dict from load_contracts()
        
    Returns:
        Normalized ContractSpec
        
    Raises:
        ContractNotFoundError: If output_id has no matching contract
    """
    # Build contract lookup
    contract_lookup = {
        contract['id']: contract
        for contract in contracts['outputs']
    }
    
    if output_id not in contract_lookup:
        available_ids = list(contract_lookup.keys())
        raise ContractNotFoundError(
            f"No contract found for output_id: '{output_id}'\n"
            f"Available contract IDs: {available_ids}\n"
            f"Ensure output_id matches a contract 'id' field exactly."
        )
    
    raw_contract = contract_lookup[output_id]
    return normalize_contract(raw_contract)


def get_all_contract_ids(contracts: Dict) -> List[str]:
    """
    Get list of all contract IDs.
    
    Args:
        contracts: Loaded contracts dict
        
    Returns:
        List of contract IDs
    """
    return [contract['id'] for contract in contracts['outputs']]
