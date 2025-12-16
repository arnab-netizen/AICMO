"""Unit tests for contract loader."""

import pytest
import os
import json
import tempfile
from pathlib import Path

from aicmo.validation.contracts import (
    load_contracts,
    get_contract_for_output,
    get_all_contract_ids,
    get_contract_path,
    ContractNotFoundError,
    ContractSchemaError,
)


def test_load_contracts_default_path():
    """Test loading contracts from default repo path."""
    contracts = load_contracts()
    
    assert 'schema_version' in contracts
    assert 'outputs' in contracts
    assert isinstance(contracts['outputs'], list)
    assert len(contracts['outputs']) > 0


def test_get_all_contract_ids():
    """Test getting list of all contract IDs."""
    contracts = load_contracts()
    contract_ids = get_all_contract_ids(contracts)
    
    assert isinstance(contract_ids, list)
    assert len(contract_ids) > 0
    
    # Should include known contracts
    assert 'marketing_strategy_report_pdf' in contract_ids


def test_get_contract_for_output_success():
    """Test getting contract for known output_id."""
    contracts = load_contracts()
    
    contract = get_contract_for_output('marketing_strategy_report_pdf', contracts)
    
    assert contract.id == 'marketing_strategy_report_pdf'
    assert contract.format == 'pdf'
    assert contract.schema_version is not None
    assert len(contract.required_sections) > 0


def test_get_contract_for_output_not_found():
    """Test getting contract for unknown output_id raises error."""
    contracts = load_contracts()
    
    with pytest.raises(ContractNotFoundError) as exc_info:
        get_contract_for_output('nonexistent_output_id', contracts)
    
    error_msg = str(exc_info.value)
    assert 'nonexistent_output_id' in error_msg
    assert 'Available contract IDs' in error_msg


def test_load_contracts_invalid_path():
    """Test loading contracts from invalid path raises error."""
    with pytest.raises(ContractNotFoundError):
        load_contracts('/nonexistent/path/contract.json')


def test_load_contracts_invalid_json():
    """Test loading invalid JSON raises schema error."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{ invalid json ')
        temp_path = f.name
    
    try:
        with pytest.raises(ContractSchemaError) as exc_info:
            load_contracts(temp_path)
        
        assert 'Invalid JSON' in str(exc_info.value)
    finally:
        os.unlink(temp_path)


def test_load_contracts_missing_schema_version():
    """Test loading contract without schema_version raises error."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({'outputs': []}, f)
        temp_path = f.name
    
    try:
        with pytest.raises(ContractSchemaError) as exc_info:
            load_contracts(temp_path)
        
        assert 'schema_version' in str(exc_info.value)
    finally:
        os.unlink(temp_path)


def test_load_contracts_missing_outputs():
    """Test loading contract without outputs raises error."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({'schema_version': '1.0.0'}, f)
        temp_path = f.name
    
    try:
        with pytest.raises(ContractSchemaError) as exc_info:
            load_contracts(temp_path)
        
        assert 'outputs' in str(exc_info.value)
    finally:
        os.unlink(temp_path)


def test_contract_spec_normalization():
    """Test contract normalization includes all expected fields."""
    contracts = load_contracts()
    contract = get_contract_for_output('marketing_strategy_report_pdf', contracts)
    
    # Check all fields are present
    assert hasattr(contract, 'id')
    assert hasattr(contract, 'schema_version')
    assert hasattr(contract, 'format')
    assert hasattr(contract, 'required_sections')
    assert hasattr(contract, 'required_strings')
    assert hasattr(contract, 'forbidden_patterns')
    assert hasattr(contract, 'min_word_count_total')
    assert hasattr(contract, 'min_word_count_by_section')
    assert hasattr(contract, 'raw_contract')


def test_get_contract_path_default():
    """Test default contract path resolution."""
    path = get_contract_path()
    
    assert path.exists()
    assert path.name == 'client_outputs.contract.json'
    assert 'tests/e2e/specs' in str(path)


def test_get_contract_path_env_var(monkeypatch):
    """Test contract path from env var."""
    # Create temp contract file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            'schema_version': '1.0.0',
            'outputs': [
                {'id': 'test', 'format': 'pdf', 'schema_version': '1.0.0'}
            ]
        }, f)
        temp_path = f.name
    
    try:
        monkeypatch.setenv('AICMO_CONTRACT_PATH', temp_path)
        path = get_contract_path()
        
        assert str(path) == temp_path
    finally:
        os.unlink(temp_path)
