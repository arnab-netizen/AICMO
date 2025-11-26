"""
Generator utility module: safe execution wrappers and helper functions.

This module prevents error text from leaking into client reports by wrapping
generator functions in safe exception handlers that return clean defaults.
"""

import logging
from typing import Callable

logger = logging.getLogger(__name__)


def safe_generate(section_name: str, fn: Callable[[], str], default: str = "") -> str:
    """
    Safely execute a section generator function.

    Wraps a generator so that:
    - Exceptions are logged, not surfaced into the client report
    - Returns either the generated string or a safe default (normally "")
    - Never leaks error tracebacks or Python exceptions to the client

    Args:
        section_name: Human-readable name of the section (for logging)
        fn: Generator function that returns a string (should accept no arguments)
        default: String to return if generation fails (default: empty string)

    Returns:
        Generated string from fn(), or default if an exception occurred

    Examples:
        >>> from aicmo.generators import overview
        >>> text = safe_generate(
        ...     "overview",
        ...     lambda: overview.generate_overview(brief, brand)
        ... )
    """
    try:
        result = fn()
        if result is None:
            return default
        return str(result)
    except Exception as e:
        logger.exception("Error generating section '%s': %s", section_name, e)
        # DO NOT leak error text to client
        return default


def safe_generate_with_args(
    section_name: str,
    fn: Callable[..., str],
    args: tuple = (),
    kwargs: dict = None,
    default: str = "",
) -> str:
    """
    Safely execute a section generator function with arguments.

    Similar to safe_generate but allows passing arguments and keyword arguments
    to the generator function.

    Args:
        section_name: Human-readable name of the section (for logging)
        fn: Generator function that returns a string
        args: Positional arguments to pass to fn()
        kwargs: Keyword arguments to pass to fn()
        default: String to return if generation fails (default: empty string)

    Returns:
        Generated string from fn(*args, **kwargs), or default if an exception occurred

    Examples:
        >>> from aicmo.generators import channel_plan
        >>> text = safe_generate_with_args(
        ...     "channel_plan",
        ...     channel_plan.generate_channel_plan,
        ...     args=(brief, brand),
        ...     kwargs={"include_budget": True}
        ... )
    """
    if kwargs is None:
        kwargs = {}

    try:
        result = fn(*args, **kwargs)
        if result is None:
            return default
        return str(result)
    except Exception as e:
        logger.exception("Error generating section '%s': %s", section_name, e)
        # DO NOT leak error text to client
        return default
