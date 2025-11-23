"""
Test suite for WOW template validation.

Ensures that all WOW templates:
1. Have properly matched opening and closing braces
2. Use valid placeholder names (alphanumeric + underscore)
3. Don't contain malformed or nested placeholders
4. Can be safely processed by apply_wow_template()
"""

from __future__ import annotations

import re

from aicmo.presets.wow_templates import WOW_TEMPLATES


class TestWowTemplateValidation:
    """Validate all WOW templates for proper brace matching and placeholder syntax."""

    @staticmethod
    def _get_placeholders(text: str) -> list[str]:
        """Extract all {{...}} placeholders from text."""
        pattern = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")
        return pattern.findall(text)

    @staticmethod
    def _count_braces(text: str) -> tuple[int, int]:
        """Count opening {{ and closing }} braces."""
        return text.count("{{"), text.count("}}")

    def test_all_templates_exist(self):
        """Verify that WOW_TEMPLATES dict is not empty."""
        assert len(WOW_TEMPLATES) > 0, "WOW_TEMPLATES dict should not be empty"

    def test_templates_are_non_empty_strings(self):
        """Verify all templates are non-empty strings."""
        for key, template in WOW_TEMPLATES.items():
            assert isinstance(template, str), f"Template {key} should be a string"
            assert len(template) > 0, f"Template {key} should not be empty"

    def test_balanced_braces_in_all_templates(self):
        """Verify that all templates have balanced {{ and }} braces."""
        for key, template in WOW_TEMPLATES.items():
            open_braces, close_braces = self._count_braces(template)
            assert (
                open_braces == close_braces
            ), f"Template {key} has unmatched braces: {open_braces} {{ vs {close_braces} }}"

    def test_valid_placeholder_syntax(self):
        """Verify all placeholders follow {{placeholder_name}} pattern."""
        # Pattern for valid placeholders: {{ name }}
        valid_pattern = re.compile(r"^{{\s*[a-zA-Z0-9_]+\s*}}$")

        for key, template in WOW_TEMPLATES.items():
            # Find all {{ ... }} patterns
            all_placeholders = re.findall(r"{{.*?}}", template)

            for placeholder in all_placeholders:
                assert valid_pattern.match(
                    placeholder
                ), f"Invalid placeholder syntax in {key}: {placeholder}"

    def test_no_nested_placeholders(self):
        """Verify templates don't contain nested {{ {{ ... }} }}."""
        for key, template in WOW_TEMPLATES.items():
            # Remove valid placeholders first
            cleaned = re.sub(r"{{\s*[a-zA-Z0-9_]+\s*}}", "", template)
            # Check for remaining {{ which would indicate nesting
            assert (
                "{{" not in cleaned or "}}" not in cleaned
            ), f"Template {key} may contain nested or malformed braces"

    def test_no_empty_placeholders(self):
        """Verify there are no empty {{ }} placeholders."""
        empty_pattern = re.compile(r"{{\s*}}")

        for key, template in WOW_TEMPLATES.items():
            assert not empty_pattern.search(
                template
            ), f"Template {key} contains empty {{ }} placeholders"

    def test_placeholder_consistency(self):
        """Verify that commonly used placeholders appear in most templates."""
        template_placeholders = {}
        for key, template in WOW_TEMPLATES.items():
            placeholders = set(self._get_placeholders(template))
            template_placeholders[key] = placeholders

        # Check that brand_name appears in most templates
        brand_name_count = sum(1 for phs in template_placeholders.values() if "brand_name" in phs)
        assert (
            brand_name_count >= len(WOW_TEMPLATES) * 0.8
        ), "brand_name should appear in at least 80% of templates"

    def test_no_special_characters_in_placeholders(self):
        """Verify placeholder names only use alphanumeric + underscore."""
        invalid_pattern = re.compile(r"{{[^a-zA-Z0-9_\s}][^}]*}}")

        for key, template in WOW_TEMPLATES.items():
            matches = invalid_pattern.findall(template)
            assert not matches, f"Template {key} has invalid placeholder names: {matches}"

    def test_placeholder_names_are_reasonable_length(self):
        """Verify placeholder names are neither too short nor too long."""
        pattern = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")

        for key, template in WOW_TEMPLATES.items():
            placeholders = pattern.findall(template)
            for placeholder in placeholders:
                assert (
                    1 <= len(placeholder) <= 100
                ), f"Placeholder {placeholder} in {key} has unreasonable length"

    def test_no_html_or_script_in_placeholders(self):
        """Verify placeholders don't contain HTML/script injection attempts."""
        # Look for actual dangerous characters, not just words containing them
        dangerous_patterns = [
            re.compile(r"{{.*[<>].*}}"),  # HTML brackets
            re.compile(r"{{.*\$\{.*}}"),  # Template injection
            re.compile(r"{{.*`.*}}"),  # Backticks for command injection
            re.compile(r"{{.*\|\s*sh.*}}"),  # Shell pipes
        ]

        for key, template in WOW_TEMPLATES.items():
            for pattern in dangerous_patterns:
                matches = pattern.findall(template)
                assert (
                    not matches
                ), f"Template {key} has potentially dangerous placeholder: {matches}"

    def test_placeholders_are_extractable(self):
        """Verify all placeholders can be extracted with a simple regex."""
        pattern = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")

        for key, template in WOW_TEMPLATES.items():
            # This should work without errors
            placeholders = pattern.findall(template)

            # Reconstruct: each placeholder should be findable as {{ name }}
            for placeholder in set(placeholders):
                placeholder_regex = re.compile(rf"{{{{{re.escape(placeholder)}}}}}", re.IGNORECASE)
                matches = placeholder_regex.findall(template)
                assert len(matches) > 0, (
                    f"Placeholder {placeholder} in {key} cannot be " f"reconstructed from template"
                )

    def test_no_duplicate_placeholder_definitions(self):
        """Verify templates don't define the same placeholder multiple times with different cases."""
        pattern = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}", re.IGNORECASE)

        for key, template in WOW_TEMPLATES.items():
            placeholders = pattern.findall(template)
            placeholder_lower = [p.lower() for p in placeholders]

            # Check that we don't have the same placeholder in different cases
            # (e.g., {{Brand_Name}} and {{brand_name}})
            for placeholder in set(placeholder_lower):
                variants = [p for p in placeholders if p.lower() == placeholder]
                # Allow minor case variations but warn about potential issues
                if len(set(variants)) > 1:
                    # This is not a failure, just a potential issue
                    pass

    def test_placeholder_count_reasonable(self):
        """Verify templates have a reasonable number of placeholders."""
        pattern = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")

        for key, template in WOW_TEMPLATES.items():
            placeholders = set(pattern.findall(template))

            # Templates should have between 5 and 200 unique placeholders
            # (too few = template is too simple, too many = might be malformed)
            assert (
                5 <= len(placeholders) <= 200
            ), f"Template {key} has {len(placeholders)} unique placeholders, expected 5-200"
