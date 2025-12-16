"""
Output Validator

Orchestrates validation of client-facing outputs against contracts.
This is the delivery gate - FAIL blocks delivery.
"""

import json
import re
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from .section_map import SectionMap
from .manifest import ArtifactManifest


@dataclass
class SectionValidation:
    """Validation result for a single section."""
    section_id: str
    title: str
    word_count: int
    word_count_valid: bool
    word_count_expected_min: int
    placeholder_scan: str  # PASS/FAIL
    forbidden_phrase_scan: str  # PASS/FAIL
    issues: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ValidationResult:
    """Validation result for a single artifact."""
    artifact_id: str
    status: str  # PASS/FAIL
    structural_checks: Dict[str, Any]
    safety_checks: Dict[str, Any]
    content_checks: Dict[str, Any]
    section_validations: List[SectionValidation]
    issues: List[str]
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'section_validations': [s.to_dict() for s in self.section_validations]
        }


@dataclass
class ValidationReport:
    """Complete validation report for a delivery."""
    validation_version: str
    run_id: str
    timestamp: str
    global_status: str  # PASS/FAIL
    artifacts: List[ValidationResult]
    proof_run_checks: Dict[str, Any]
    determinism_checks: Dict[str, Any]
    metadata: Dict
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'artifacts': [a.to_dict() for a in self.artifacts]
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def save(self, filepath: str) -> None:
        """Save validation report to file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())
    
    @property
    def is_pass(self) -> bool:
        """Check if validation passed."""
        return self.global_status == "PASS"
    
    def get_failure_summary(self) -> str:
        """Get human-readable summary of failures."""
        if self.is_pass:
            return "All validations passed."
        
        failures = []
        for artifact in self.artifacts:
            if artifact.status != "PASS":
                failures.append(f"\n{artifact.artifact_id}:")
                failures.extend(f"  - {issue}" for issue in artifact.issues)
        
        return "\n".join(failures)


class OutputValidator:
    """Validates client-facing outputs against contracts."""
    
    VALIDATION_VERSION = "1.0.0"
    
    def __init__(self, contract_path: str):
        """
        Initialize validator with contract file.
        
        Args:
            contract_path: Path to client_outputs.contract.json
        """
        with open(contract_path, 'r') as f:
            self.contracts = json.load(f)
        
        self.output_contracts = {
            contract['id']: contract
            for contract in self.contracts['outputs']
        }
    
    def get_contract(self, artifact_id: str) -> Dict:
        """Get contract for an artifact."""
        if artifact_id not in self.output_contracts:
            raise ValueError(f"No contract found for artifact: {artifact_id}")
        return self.output_contracts[artifact_id]
    
    def validate_placeholders(self, text: str, contract: Dict) -> tuple[bool, List[str]]:
        """
        Validate no forbidden placeholders exist.
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        forbidden_patterns = contract.get('forbidden_patterns', [])
        dynamic_allowlist = contract.get('dynamic_allowlist_patterns', [])
        
        for pattern in forbidden_patterns:
            # Skip if it's in the allowlist
            if pattern in dynamic_allowlist:
                continue
            
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                issues.append(f"Forbidden pattern found: {pattern} (matches: {matches[:3]})")
        
        return len(issues) == 0, issues
    
    def validate_required_strings(self, text: str, contract: Dict) -> tuple[bool, List[str]]:
        """
        Validate required strings are present.
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        required_strings = contract.get('required_strings', [])
        dynamic_allowlist = contract.get('dynamic_allowlist_patterns', [])
        
        for required_str in required_strings:
            # If it's a template variable, skip validation (will be substituted)
            if required_str in dynamic_allowlist:
                continue
            
            # For non-template strings, check exact match
            if required_str not in text:
                issues.append(f"Required string not found: {required_str}")
        
        return len(issues) == 0, issues
    
    def validate_section_map(
        self,
        section_map: SectionMap,
        contract: Dict
    ) -> List[SectionValidation]:
        """
        Validate section map against contract.
        
        Returns:
            List of section validation results
        """
        section_validations = []
        required_sections = contract.get('required_sections', [])
        min_word_counts = contract.get('min_word_count_by_section', {})
        
        # Check all required sections are present
        section_titles = [s.section_title for s in section_map.sections]
        missing_sections = set(required_sections) - set(section_titles)
        
        if missing_sections:
            # Create failed validations for missing sections
            for section_title in missing_sections:
                section_validations.append(SectionValidation(
                    section_id="missing",
                    title=section_title,
                    word_count=0,
                    word_count_valid=False,
                    word_count_expected_min=min_word_counts.get(section_title, 0),
                    placeholder_scan="FAIL",
                    forbidden_phrase_scan="FAIL",
                    issues=[f"Section missing: {section_title}"]
                ))
        
        # Validate existing sections
        forbidden_patterns = contract.get('forbidden_patterns', [])
        
        for section in section_map.sections:
            expected_min = min_word_counts.get(section.section_title, 0)
            word_count_valid = section.word_count >= expected_min
            
            issues = []
            if not word_count_valid:
                issues.append(
                    f"Word count too low: {section.word_count} < {expected_min}"
                )
            
            # Check forbidden patterns in section title (DETERMINISTIC - source of truth)
            placeholder_scan = "PASS"
            forbidden_phrase_scan = "PASS"
            
            for pattern in forbidden_patterns:
                # Check section title
                if re.search(pattern, section.section_title, re.IGNORECASE):
                    forbidden_phrase_scan = "FAIL"
                    issues.append(
                        f"Forbidden pattern '{pattern}' found in section title: '{section.section_title}'"
                    )
            
            section_validations.append(SectionValidation(
                section_id=section.section_id,
                title=section.section_title,
                word_count=section.word_count,
                word_count_valid=word_count_valid,
                word_count_expected_min=expected_min,
                placeholder_scan=placeholder_scan,
                forbidden_phrase_scan=forbidden_phrase_scan,
                issues=issues
            ))
        
        return section_validations
    
    def validate_artifact(
        self,
        artifact_id: str,
        filepath: str,
        section_map: Optional[SectionMap] = None
    ) -> ValidationResult:
        """
        Validate a single artifact.
        
        Args:
            artifact_id: Artifact identifier from contract
            filepath: Path to artifact file
            section_map: Optional section map for content validation
            
        Returns:
            ValidationResult
        """
        contract = self.get_contract(artifact_id)
        issues = []
        
        # Import validators dynamically based on format
        from tests.e2e.output_validators import get_validator
        
        format_type = contract['format']
        validator = get_validator(format_type)
        
        # Structural validation
        structural_checks = validator.validate_structure(filepath, contract)
        if not structural_checks.get('valid', False):
            issues.extend(structural_checks.get('errors', []))
        
        # Safety validation
        safety_checks = validator.validate_safety(filepath, contract)
        if not safety_checks.get('valid', False):
            issues.extend(safety_checks.get('errors', []))
        
        # Content validation (if section map provided)
        content_checks = {}
        section_validations = []
        
        if section_map:
            section_validations = self.validate_section_map(section_map, contract)
            
            # Check if any section validations failed
            failed_sections = [s for s in section_validations if s.issues]
            if failed_sections:
                issues.extend([
                    f"Section '{s.title}': {', '.join(s.issues)}"
                    for s in failed_sections
                ])
            
            content_checks = {
                'section_count': len(section_map.sections),
                'total_word_count': section_map.total_word_count,
                'min_word_count': contract.get('min_word_count_total', 0),
                'word_count_valid': section_map.total_word_count >= contract.get('min_word_count_total', 0)
            }
        
        # Determine overall status
        status = "PASS" if len(issues) == 0 else "FAIL"
        
        return ValidationResult(
            artifact_id=artifact_id,
            status=status,
            structural_checks=structural_checks,
            safety_checks=safety_checks,
            content_checks=content_checks,
            section_validations=section_validations,
            issues=issues
        )
    
    def validate_manifest(
        self,
        manifest: ArtifactManifest,
        section_maps: Optional[Dict[str, SectionMap]] = None
    ) -> ValidationReport:
        """
        Validate all artifacts in a manifest.
        
        Args:
            manifest: Artifact manifest
            section_maps: Optional dict of artifact_id -> SectionMap
            
        Returns:
            Complete ValidationReport
        """
        artifact_results = []
        section_maps = section_maps or {}
        
        for artifact in manifest.artifacts:
            section_map = section_maps.get(artifact.artifact_id)
            
            try:
                result = self.validate_artifact(
                    artifact_id=artifact.artifact_id,
                    filepath=artifact.path,
                    section_map=section_map
                )
                artifact_results.append(result)
            except Exception as e:
                # Validation error - mark as FAIL
                artifact_results.append(ValidationResult(
                    artifact_id=artifact.artifact_id,
                    status="FAIL",
                    structural_checks={'valid': False, 'error': str(e)},
                    safety_checks={},
                    content_checks={},
                    section_validations=[],
                    issues=[f"Validation exception: {str(e)}"]
                ))
        
        # Determine global status
        all_passed = all(r.status == "PASS" for r in artifact_results)
        global_status = "PASS" if all_passed else "FAIL"
        
        return ValidationReport(
            validation_version=self.VALIDATION_VERSION,
            run_id=manifest.run_id,
            timestamp=datetime.utcnow().isoformat(),
            global_status=global_status,
            artifacts=artifact_results,
            proof_run_checks={
                'no_external_sends': True,  # Will be filled by proof run ledger
                'no_unexpected_egress': True  # Will be filled by egress lock
            },
            determinism_checks={
                'stable_manifest': True,  # Will be filled by determinism tests
                'no_duplicate_deliveries': True
            },
            metadata={
                'contract_version': self.contracts['contract_version'],
                'total_artifacts': len(artifact_results),
                'passed_artifacts': sum(1 for r in artifact_results if r.status == "PASS"),
                'failed_artifacts': sum(1 for r in artifact_results if r.status != "PASS")
            }
        )
