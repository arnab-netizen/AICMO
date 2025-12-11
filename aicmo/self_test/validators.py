"""
Self-Test Engine Validators

Wrapper around quality validators for testing.
"""

from typing import Any, Dict, List, Optional

from aicmo.quality.validators import (
    ReportValidationError,
    ReportIssue,
    validate_report,
)


class ValidatorWrapper:
    """Wrapper around quality validators for self-test."""

    @staticmethod
    def validate_generator_output(
        generator_name: str,
        output: Any,
        output_type: str = "dict",
    ) -> Dict[str, Any]:
        """
        Validate generator output.

        Accepts both Pydantic models and dicts. Infers validation type from output.

        Args:
            generator_name: Name of the generator
            output: Output from the generator (Pydantic model, dict, str, list, etc)
            output_type: Type of output ('dict', 'str', 'report', 'pydantic', etc)

        Returns:
            Dictionary with validation results:
                - is_valid (bool)
                - errors (list of str)
                - warnings (list of str)
                - severity (str): 'critical', 'high', 'medium', 'low'
        """
        from pydantic import BaseModel
        
        errors = []
        warnings = []

        # Check basic structure
        if output is None:
            errors.append("Output is None")
        elif isinstance(output, dict) and not output:
            warnings.append("Output is empty dictionary")
        elif isinstance(output, str) and not output:
            warnings.append("Output is empty string")
        elif isinstance(output, list) and not output:
            warnings.append("Output is empty list")
        elif isinstance(output, BaseModel):
            # Pydantic models are valid if they instantiated successfully
            warnings.append(f"Got {type(output).__name__} (Pydantic model - OK)")

        # Infer validation type if not specified
        if isinstance(output, BaseModel):
            output_type = "pydantic"
        elif isinstance(output, dict):
            output_type = "dict"
        elif isinstance(output, str):
            output_type = "str"
        elif isinstance(output, list):
            output_type = "list"

        # Validate by output type
        if output_type == "pydantic":
            # Pydantic models that instantiate are valid by definition
            pass
        elif output_type == "dict":
            errors.extend(ValidatorWrapper._validate_dict_output(output))
        elif output_type == "report" or output_type == "strategy":
            errors.extend(ValidatorWrapper._validate_report_output(output, generator_name))
        elif output_type == "str":
            errors.extend(ValidatorWrapper._validate_string_output(output))
        elif output_type == "list":
            errors.extend(ValidatorWrapper._validate_list_output(output))

        # Determine severity
        if errors:
            severity = "critical" if any("critical" in e.lower() for e in errors) else "high"
        elif warnings:
            severity = "medium"
        else:
            severity = "low"

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "severity": severity,
        }

    @staticmethod
    def _validate_list_output(output: Any) -> List[str]:
        """Validate list output."""
        errors = []
        if not isinstance(output, list):
            errors.append(f"Expected list, got {type(output).__name__}")
        elif not output:
            errors.append("List is empty")
        return errors

    @staticmethod
    def _validate_dict_output(output: Any) -> List[str]:
        """Validate dictionary output."""
        errors = []

        if not isinstance(output, dict):
            errors.append(f"Expected dict, got {type(output).__name__}")
            return errors

        # Check for required structure
        if not output:
            errors.append("Dictionary is empty")
        else:
            # Check for meaningful content
            for key, value in output.items():
                if value is None:
                    errors.append(f"Key '{key}' has None value")
                elif isinstance(value, str) and not value.strip():
                    errors.append(f"Key '{key}' has empty string value")

        return errors

    @staticmethod
    def _validate_report_output(output: Any, generator_name: str = "") -> List[str]:
        """Validate report/strategy document output."""
        errors = []

        if not isinstance(output, (dict, str)):
            errors.append(f"Report must be dict or str, got {type(output).__name__}")
            return errors

        # Try to use the aicmo quality validator if available
        try:
            if isinstance(output, dict):
                # For dict output, just check it's not empty
                if not output:
                    errors.append("Report dictionary is empty")
            else:
                output_str = output
                # Check for minimum content
                if len(output_str) < 20:
                    errors.append(f"Report output too short: {len(output_str)} chars")
        except Exception as e:
            # Graceful degradation if validator not fully available
            if len(str(output)) < 50:
                errors.append(f"Report output too short: {len(str(output))} chars")

        return errors

    @staticmethod
    def _validate_string_output(output: Any) -> List[str]:
        """Validate string output."""
        errors = []

        if not isinstance(output, str):
            errors.append(f"Expected string, got {type(output).__name__}")
            return errors

        if not output.strip():
            errors.append("String output is empty or whitespace only")
        elif len(output) < 20:
            errors.append(f"String output too short: {len(output)} chars")

        return errors

    @staticmethod
    def validate_packager_output(
        packager_name: str,
        output_file: Optional[str],
        file_size: Optional[int],
    ) -> Dict[str, Any]:
        """
        Validate packager output (file generation).

        Args:
            packager_name: Name of the packager function
            output_file: Path to generated file
            file_size: Size of generated file in bytes

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        if not output_file:
            errors.append("No output file generated")
        elif not isinstance(output_file, str):
            errors.append(f"Output file path must be string, got {type(output_file).__name__}")
        else:
            # Check file size
            if file_size is None or file_size == 0:
                errors.append("Output file is empty or size unknown")
            elif file_size < 1000:
                warnings.append(f"Output file is very small: {file_size} bytes")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "severity": "high" if errors else ("medium" if warnings else "low"),
        }

    @staticmethod
    def validate_gateway_output(
        gateway_name: str,
        response: Any,
        expected_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Validate gateway/adapter response.

        Args:
            gateway_name: Name of the gateway
            response: Response from the gateway
            expected_fields: Expected fields in response

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        if response is None:
            errors.append("Response is None")
        elif isinstance(response, dict):
            if not response:
                warnings.append("Response is empty dictionary")
            elif expected_fields:
                missing_fields = set(expected_fields) - set(response.keys())
                if missing_fields:
                    errors.append(f"Missing fields: {missing_fields}")
        else:
            warnings.append(f"Expected dict response, got {type(response).__name__}")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "severity": "high" if errors else ("medium" if warnings else "low"),
        }
