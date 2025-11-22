"""
LLM safety module for timeouts, input size limits, and graceful error handling.

Prevents:
- Long hangs from slow LLM APIs
- Overload from extremely large inputs
- Crashes from malformed content

Provides:
- Automatic truncation of oversized inputs
- Timeout enforcement on LLM calls
- Structured logging of safety events
- Graceful fallback on failures
"""

import logging
from typing import Optional

logger = logging.getLogger("aicmo.llm_safety")

# Configuration: These can be overridden via environment variables
DEFAULT_LLM_TIMEOUT = 30  # seconds
DEFAULT_MAX_SECTION_CHARS = 10000  # per section
DEFAULT_MAX_PROMPT_CHARS = 30000  # combined prompt

# Thresholds for truncation warnings
WARN_SECTION_THRESHOLD = 8000
WARN_PROMPT_THRESHOLD = 25000


def _truncate_text(text: Optional[str], max_chars: int, label: str = "text") -> tuple[str, bool]:
    """
    Truncate text to max_chars if needed, return (truncated_text, was_truncated).

    Args:
        text: Text to potentially truncate
        max_chars: Maximum characters allowed
        label: Label for logging (e.g., "brief", "marketing_plan")

    Returns:
        (truncated_text, was_truncated) tuple
    """
    if not text:
        return text or "", False

    text_str = str(text)
    if len(text_str) <= max_chars:
        return text_str, False

    # Truncate at a word boundary near the limit
    truncated = text_str[:max_chars]

    # Try to find the last space to avoid cutting mid-word
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.8:  # If space is at least 80% through
        truncated = truncated[:last_space].strip()

    logger.warning(
        f"LLM input truncation: {label} exceeded {max_chars} chars "
        f"({len(text_str)} -> {len(truncated)} chars)"
    )

    return truncated, True


def validate_llm_input_size(
    brief_dict: dict,
    output_dict: dict,
    max_section_chars: int = DEFAULT_MAX_SECTION_CHARS,
    max_prompt_chars: int = DEFAULT_MAX_PROMPT_CHARS,
) -> tuple[dict, dict, bool]:
    """
    Validate and truncate LLM input to safe sizes.

    Args:
        brief_dict: Client brief as dict
        output_dict: AICMO output as dict
        max_section_chars: Max chars per section
        max_prompt_chars: Max combined prompt size

    Returns:
        (truncated_brief, truncated_output, any_truncation_occurred)

    Design: Gracefully truncates oversized inputs and logs, never crashes.
    """
    truncated_brief = dict(brief_dict)
    truncated_output = dict(output_dict)
    any_truncation = False

    # Truncate brief fields
    if "brand" in truncated_brief and isinstance(truncated_brief["brand"], dict):
        for key in ["brand_name", "tagline"]:
            if key in truncated_brief["brand"]:
                text, was_trunc = _truncate_text(
                    truncated_brief["brand"][key],
                    max_section_chars,
                    f"brief.brand.{key}",
                )
                truncated_brief["brand"][key] = text
                any_truncation = any_truncation or was_trunc

    # Truncate output marketing plan if present
    if "marketing_plan" in truncated_output and isinstance(
        truncated_output["marketing_plan"], dict
    ):
        mp = truncated_output["marketing_plan"]
        for key in ["executive_summary", "situation_analysis", "strategy"]:
            if key in mp:
                text, was_trunc = _truncate_text(
                    mp[key],
                    max_section_chars,
                    f"output.marketing_plan.{key}",
                )
                mp[key] = text
                any_truncation = any_truncation or was_trunc

    # Check total size
    import json

    try:
        brief_json = json.dumps(truncated_brief)
        output_json = json.dumps(truncated_output)
        combined_size = len(brief_json) + len(output_json)

        if combined_size > WARN_PROMPT_THRESHOLD:
            logger.warning(
                f"Combined LLM prompt size: {combined_size} chars (near limit of {max_prompt_chars})"
            )

        if combined_size > max_prompt_chars:
            logger.error(
                f"Combined LLM prompt exceeds limit: {combined_size} > {max_prompt_chars}. "
                "Output and brief may need further truncation or splitting."
            )
    except Exception as e:
        logger.warning(f"Could not compute combined size: {e}")

    return truncated_brief, truncated_output, any_truncation


class LLMCallWithTimeout:
    """
    Context manager / helper for making LLM calls with timeout.

    Usage:
        result = LLMCallWithTimeout.call(
            lambda: client.messages.create(...),
            timeout=30,
            label="marketing_plan_generation"
        )
    """

    @staticmethod
    def call(
        func,
        timeout: int = DEFAULT_LLM_TIMEOUT,
        label: str = "llm_call",
    ):
        """
        Execute a callable with timeout handling.

        Args:
            func: Callable that makes the LLM call
            timeout: Timeout in seconds
            label: Label for logging

        Returns:
            Result from func, or None if timeout/error

        Design: Catches timeout + other exceptions, logs, returns None for fallback handling.
        """
        import signal

        class TimeoutError(Exception):
            """Timeout exceeded."""

            pass

        def timeout_handler(signum, frame):
            raise TimeoutError(f"{label} exceeded {timeout}s")

        try:
            # Set signal alarm for timeout
            # Note: This only works on Unix; Windows would need concurrent.futures
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)

            try:
                result = func()
                signal.alarm(0)  # Cancel the alarm
                logger.info(f"{label} completed within {timeout}s")
                return result
            except TimeoutError as e:
                logger.warning(f"LLM timeout: {e}")
                return None
            except Exception as e:
                signal.alarm(0)  # Cancel alarm on other errors
                logger.error(f"LLM call failed ({label}): {e}", exc_info=False)
                return None
        except Exception as e:
            logger.error(f"Unexpected error in LLM safety wrapper: {e}", exc_info=True)
            return None


def safe_llm_enhancement(
    llm_enhance_func,
    brief,
    stub_output,
    options: dict = None,
    timeout: int = DEFAULT_LLM_TIMEOUT,
) -> Optional[dict]:
    """
    Wrapper around LLM enhancement with safety checks.

    Args:
        llm_enhance_func: Function that does LLM enhancement
        brief: ClientInputBrief
        stub_output: Dict of stub output
        options: Options dict for enhancement function
        timeout: Timeout in seconds

    Returns:
        Enhanced output dict, or stub_output on failure

    Design: Non-breaking; always returns something. Logs issues. Respects timeout.
    """
    options = options or {}

    try:
        # Validate input size
        brief_dict = brief.model_dump() if hasattr(brief, "model_dump") else brief
        stub_dict = stub_output if isinstance(stub_output, dict) else stub_output.model_dump()

        brief_dict, stub_dict, any_trunc = validate_llm_input_size(brief_dict, stub_dict)

        if any_trunc:
            logger.info("Input was truncated due to size limits; LLM may produce partial results")

        # Call with timeout
        result = LLMCallWithTimeout.call(
            lambda: llm_enhance_func(brief, stub_dict, options),
            timeout=timeout,
            label="llm_enhancement",
        )

        if result is None:
            logger.warning("LLM enhancement failed or timed out; returning stub output")
            return stub_dict

        return result

    except Exception as e:
        logger.error(f"Unexpected error in safe_llm_enhancement: {e}", exc_info=True)
        return stub_output if isinstance(stub_output, dict) else stub_output.model_dump()
