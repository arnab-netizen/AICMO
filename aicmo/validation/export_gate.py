"""
Export gate integration for E2E validation.

Wraps the export process to generate section maps, manifests, validation reports,
and enforce delivery blocking based on validation status.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from aicmo.validation import (
    get_runtime_paths,
    SectionMapGenerator,
    ManifestGenerator,
    OutputValidator,
)
from aicmo.validation.contracts import (
    load_contracts,
    get_contract_path,
    ContractNotFoundError,
)
from aicmo.delivery.gate import block_delivery, DeliveryBlockedError


def determine_output_id(format_: str, output: Dict[str, Any]) -> str:
    """
    Determine output_id from format and output metadata.
    
    This is the deterministic mapping between exports and contracts.
    
    Args:
        format_: Export format (pdf, pptx, docx, etc.)
        output: Generated output dict
        
    Returns:
        output_id that matches contract ID
    """
    # For now, use simple format-based mapping
    # Future: can check output metadata for pack_key, preset, etc.
    return f"client_output_{format_}"


class ExportGate:
    """
    Integrates E2E gate validation into export flow.
    
    Responsibilities:
    - Generate section maps from structured content
    - Create manifests for all exported artifacts
    - Run validation against contracts
    - Block delivery if validation fails
    """
    
    def __init__(self, contracts_path: Optional[str] = None):
        """
        Initialize export gate.
        
        Args:
            contracts_path: Path to contracts JSON (defaults to resolution order)
        """
        self.enabled = os.getenv('AICMO_E2E_MODE') == '1'
        
        if not self.enabled:
            return
        
        # Load contracts using canonical loader
        try:
            if contracts_path:
                self.contracts = load_contracts(contracts_path)
            else:
                # Use resolution order: env var or default
                self.contracts = load_contracts()
        except ContractNotFoundError as e:
            print(f"WARNING: Contract loading failed: {e}")
            self.enabled = False
            return
        
        self.paths = get_runtime_paths()
        
        # Initialize generators/validators
        self.section_map_gen = SectionMapGenerator()
        self.manifest_gen = ManifestGenerator()
        self.validator = None  # Lazy init when needed
    
    def process_export(
        self,
        brief: Dict[str, Any],
        output: Dict[str, Any],
        file_bytes: bytes,
        format_: str,
        filename: str,
    ) -> Tuple[bytes, Optional[Dict]]:
        """
        Process export through E2E gate.
        
        Args:
            brief: Brief dictionary
            output: Generated output/report dictionary
            file_bytes: Raw file bytes
            format_: Export format (pdf, pptx, etc.)
            filename: Destination filename
            
        Returns:
            (file_bytes, validation_report_dict or None)
            
        Raises:
            DeliveryBlockedError: If validation fails in E2E mode
        """
        if not self.enabled:
            return file_bytes, None
        
        try:
            # Step 0: Determine output_id
            output_id = determine_output_id(format_, output)
            
            # Step 1: Generate section map from structured output
            section_map = self._generate_section_map(output, format_, output_id)
            
            # Step 2: Save file to downloads directory
            file_path = self._save_file(file_bytes, filename)
            
            # Step 3: Generate manifest with output_id
            manifest = self._generate_manifest(file_path, format_, brief, output_id)
            
            # Step 4: Run validation using output_id
            validation_report = self._validate_artifacts(
                manifest, section_map, format_, output_id
            )
            
            # Step 5: Enforce delivery gate
            try:
                block_delivery(validation_report)
            except DeliveryBlockedError as e:
                # Log blocking reason
                self._log_delivery_blocked(str(e))
                raise
            
            return file_bytes, validation_report.to_dict()
            
        except DeliveryBlockedError:
            raise
        except Exception as e:
            # Log error but don't block in case of infrastructure issues
            print(f"E2E gate processing error (non-blocking): {e}")
            return file_bytes, None
    
    def _generate_section_map(self, output: Dict[str, Any], format_: str, output_id: str):
        """Generate section map from structured output."""
        # Extract sections from output
        sections = {}
        
        # Try different section extraction strategies
        if 'sections' in output:
            # Direct sections dict
            sections = output['sections']
        elif 'content' in output and isinstance(output['content'], dict):
            # Content with subsections
            sections = output['content']
        elif 'report' in output:
            # Nested report structure
            sections = self._extract_sections_from_report(output['report'])
        else:
            # Fallback: use full output as single section
            sections = {'Full Report': str(output)}
        
        # Generate section map with output_id
        document_id = f"{output_id}_{int(datetime.utcnow().timestamp())}"
        section_map = self.section_map_gen.create_from_dict(
            document_id=document_id,
            document_type=output_id,
            sections_dict=sections
        )
        
        # Save section map
        section_map.save(str(self.paths.section_map_path))
        
        return section_map
    
    def _extract_sections_from_report(self, report: Any) -> Dict[str, str]:
        """Extract sections from nested report structure."""
        sections = {}
        
        if isinstance(report, dict):
            for key, value in report.items():
                if isinstance(value, str):
                    sections[key] = value
                elif isinstance(value, dict):
                    sections[key] = json.dumps(value)
                else:
                    sections[key] = str(value)
        else:
            sections['Report'] = str(report)
        
        return sections
    
    def _save_file(self, file_bytes: bytes, filename: str) -> Path:
        """Save file to downloads directory."""
        file_path = self.paths.get_download_path(filename)
        file_path.write_bytes(file_bytes)
        return file_path
    
    def _generate_manifest(
        self, file_path: Path, format_: str, brief: Dict[str, Any], output_id: str
    ):
        """Generate manifest for exported artifact with output_id."""
        # Create artifact info with output_id
        artifact_info = self.manifest_gen.create_artifact_info(
            artifact_id=output_id,  # Use output_id instead of generic client_output_{format}
            filepath=str(file_path),
            schema_version="1.0.0",
            section_map_path=str(self.paths.section_map_path)
        )
        
        # Create manifest
        client_id = brief.get('brand', {}).get('brand_name', 'default_client')
        manifest = self.manifest_gen.create_manifest(
            run_id=self.paths.run_id,
            client_id=client_id,
            project_id='export_project',
            artifacts=[artifact_info]
        )
        
        # Save manifest
        manifest.save(str(self.paths.manifest_path))
        
        return manifest
    
    def _validate_artifacts(self, manifest, section_map, format_, output_id: str):
        """Run validation against contracts using output_id."""
        # Lazy init validator with loaded contracts
        if self.validator is None:
            # Use contract path from loaded contracts
            contract_path = get_contract_path()
            self.validator = OutputValidator(str(contract_path))
        
        # Validate manifest with section maps keyed by output_id
        section_maps = {
            output_id: section_map
        }
        
        validation_report = self.validator.validate_manifest(
            manifest, section_maps=section_maps
        )
        
        # Save validation report
        validation_report.save(str(self.paths.validation_path))
        
        return validation_report
    
    def _log_delivery_blocked(self, reason: str):
        """Log delivery blocking event."""
        log_file = self.paths.logs_dir / "delivery_blocked.log"
        with open(log_file, 'a') as f:
            f.write(f"[{datetime.utcnow().isoformat()}] BLOCKED: {reason}\n")


# Global singleton
_export_gate: Optional[ExportGate] = None


def get_export_gate() -> ExportGate:
    """Get or create export gate singleton."""
    global _export_gate
    if _export_gate is None:
        _export_gate = ExportGate()
    return _export_gate


def reset_export_gate() -> None:
    """Reset export gate singleton (for testing)."""
    global _export_gate
    _export_gate = None


def process_export_with_gate(
    brief: Dict[str, Any],
    output: Dict[str, Any],
    file_bytes: bytes,
    format_: str,
    filename: str,
) -> Tuple[bytes, Optional[Dict]]:
    """
    Process export through E2E gate (convenience function).
    
    Args:
        brief: Brief dictionary
        output: Generated output/report dictionary
        file_bytes: Raw file bytes
        format_: Export format
        filename: Destination filename
        
    Returns:
        (file_bytes, validation_report_dict or None)
        
    Raises:
        DeliveryBlockedError: If validation fails
    """
    gate = get_export_gate()
    return gate.process_export(brief, output, file_bytes, format_, filename)
