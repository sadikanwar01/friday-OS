"""
FRIDAY OS — Input Validation Utilities.

Every validator in this module raises
:class:`~backend.utils.exceptions.FridayValidationError` on failure and
returns the validated (possibly transformed) value on success.

Usage::

    from backend.utils.validators import validate_url, validate_port

    url = validate_url("https://example.com")
    port = validate_port(8080)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from backend.utils.exceptions import FridayValidationError

# ---------------------------------------------------------------------------
# String / value validators
# ---------------------------------------------------------------------------


def validate_not_empty(value: str, field_name: str) -> str:
    """Validate that *value* is a non-empty string after stripping whitespace.

    Args:
        value: The string to check.
        field_name: Human-readable field name for the error message.

    Returns:
        The stripped, non-empty string.

    Raises:
        FridayValidationError: If *value* is empty or whitespace-only.
    """
    if not isinstance(value, str):
        raise FridayValidationError(
            message=f"'{field_name}' must be a string, got {type(value).__name__}",
            error_code="VALIDATION_TYPE",
            details={"field": field_name, "received_type": type(value).__name__},
        )
    stripped = value.strip()
    if not stripped:
        raise FridayValidationError(
            message=f"'{field_name}' must not be empty",
            error_code="VALIDATION_EMPTY",
            details={"field": field_name},
        )
    return stripped


def validate_enum_value(value: str, allowed: list[str], field_name: str) -> str:
    """Validate that *value* is one of the *allowed* values.

    Args:
        value: The value to check.
        allowed: List of acceptable values.
        field_name: Human-readable field name for the error message.

    Returns:
        The validated value (unchanged).

    Raises:
        FridayValidationError: If *value* is not in *allowed*.
    """
    if value not in allowed:
        raise FridayValidationError(
            message=(f"Invalid value '{value}' for '{field_name}'. Allowed: {', '.join(allowed)}"),
            error_code="VALIDATION_ENUM",
            details={"field": field_name, "value": value, "allowed": allowed},
        )
    return value


# ---------------------------------------------------------------------------
# Path / file validators
# ---------------------------------------------------------------------------


def validate_path_safe(path: str) -> Path:
    """Validate that *path* does not contain directory-traversal sequences.

    The function rejects paths containing ``..`` components, prevents null
    bytes, and returns a resolved :class:`~pathlib.Path`.

    Args:
        path: Raw path string to validate.

    Returns:
        A resolved :class:`~pathlib.Path` object.

    Raises:
        FridayValidationError: If the path contains traversal or unsafe
            characters.
    """
    if not path or not path.strip():
        raise FridayValidationError(
            message="Path must not be empty",
            error_code="VALIDATION_PATH_EMPTY",
            details={"path": path},
        )

    # Null-byte check
    if "\x00" in path:
        raise FridayValidationError(
            message="Path contains null bytes",
            error_code="VALIDATION_PATH_NULL",
            details={"path": repr(path)},
        )

    # Traversal check — reject any ".." component regardless of separator
    normalised = path.replace("\\", "/")
    parts = normalised.split("/")
    if ".." in parts:
        raise FridayValidationError(
            message="Path contains directory traversal (..)",
            error_code="VALIDATION_PATH_TRAVERSAL",
            details={"path": path},
        )

    return Path(path).resolve()


def validate_file_extension(filename: str, allowed_extensions: list[str]) -> str:
    """Validate that *filename* has one of the *allowed_extensions*.

    Extension comparison is case-insensitive.  Leading dots in
    *allowed_extensions* are optional (both ``".py"`` and ``"py"`` work).

    Args:
        filename: Filename to check.
        allowed_extensions: List of allowed extensions.

    Returns:
        The validated filename (unchanged).

    Raises:
        FridayValidationError: If the extension is not allowed.
    """
    if not filename or not filename.strip():
        raise FridayValidationError(
            message="Filename must not be empty",
            error_code="VALIDATION_FILENAME_EMPTY",
            details={"filename": filename},
        )

    # Normalise allowed extensions to include leading dot, lowercase
    normalised_allowed = [
        ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in allowed_extensions
    ]

    suffix = Path(filename).suffix.lower()
    if suffix not in normalised_allowed:
        raise FridayValidationError(
            message=(
                f"File extension '{suffix}' is not allowed. "
                f"Allowed: {', '.join(normalised_allowed)}"
            ),
            error_code="VALIDATION_FILE_EXTENSION",
            details={
                "filename": filename,
                "extension": suffix,
                "allowed": normalised_allowed,
            },
        )
    return filename


# ---------------------------------------------------------------------------
# Network validators
# ---------------------------------------------------------------------------


def validate_url(url: str) -> str:
    """Validate that *url* is a well-formed HTTP or HTTPS URL.

    Args:
        url: URL string to validate.

    Returns:
        The validated URL (unchanged).

    Raises:
        FridayValidationError: If the URL is malformed or uses an
            unsupported scheme.
    """
    if not url or not url.strip():
        raise FridayValidationError(
            message="URL must not be empty",
            error_code="VALIDATION_URL_EMPTY",
            details={"url": url},
        )

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise FridayValidationError(
            message=f"URL scheme must be 'http' or 'https', got '{parsed.scheme}'",
            error_code="VALIDATION_URL_SCHEME",
            details={"url": url, "scheme": parsed.scheme},
        )

    if not parsed.netloc:
        raise FridayValidationError(
            message="URL must contain a valid host/netloc",
            error_code="VALIDATION_URL_HOST",
            details={"url": url},
        )

    return url


def validate_port(port: int) -> int:
    """Validate that *port* is within the valid TCP/UDP range (1–65535).

    Args:
        port: Port number to validate.

    Returns:
        The validated port number.

    Raises:
        FridayValidationError: If the port is out of range.
    """
    if not isinstance(port, int):
        raise FridayValidationError(
            message=f"Port must be an integer, got {type(port).__name__}",
            error_code="VALIDATION_PORT_TYPE",
            details={"port": port, "received_type": type(port).__name__},
        )
    if port < 1 or port > 65535:
        raise FridayValidationError(
            message=f"Port must be between 1 and 65535, got {port}",
            error_code="VALIDATION_PORT_RANGE",
            details={"port": port},
        )
    return port


# ---------------------------------------------------------------------------
# JSON validator
# ---------------------------------------------------------------------------


def validate_json_string(value: str) -> dict[str, Any]:
    """Parse and validate a JSON string, returning the decoded object.

    Args:
        value: A JSON-encoded string.

    Returns:
        The parsed dictionary.

    Raises:
        FridayValidationError: If *value* is not valid JSON or is not a
            JSON object (dict).
    """
    if not isinstance(value, str):
        raise FridayValidationError(
            message=f"Expected a JSON string, got {type(value).__name__}",
            error_code="VALIDATION_JSON_TYPE",
            details={"received_type": type(value).__name__},
        )
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, ValueError) as exc:
        raise FridayValidationError(
            message=f"Invalid JSON: {exc}",
            error_code="VALIDATION_JSON_DECODE",
            details={"value_preview": value[:200]},
        ) from exc

    if not isinstance(parsed, dict):
        raise FridayValidationError(
            message=f"Expected a JSON object (dict), got {type(parsed).__name__}",
            error_code="VALIDATION_JSON_OBJECT",
            details={"parsed_type": type(parsed).__name__},
        )
    return parsed


# ---------------------------------------------------------------------------
# Sanitisers
# ---------------------------------------------------------------------------

# Characters considered unsafe in filenames across OS platforms.
_UNSAFE_FILENAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_MAX_INPUT_LENGTH = 10_000


def sanitize_filename(filename: str) -> str:
    """Remove or replace characters that are unsafe in filenames.

    Strips leading/trailing whitespace and dots, replaces unsafe characters
    with underscores, and truncates to 255 characters.

    Args:
        filename: Raw filename to sanitise.

    Returns:
        A sanitised filename string.

    Raises:
        FridayValidationError: If the resulting filename is empty.
    """
    if not filename:
        raise FridayValidationError(
            message="Filename must not be empty",
            error_code="VALIDATION_FILENAME_EMPTY",
            details={"filename": filename},
        )

    sanitised = _UNSAFE_FILENAME_RE.sub("_", filename)
    sanitised = sanitised.strip(". ")

    # Truncate to filesystem limit
    sanitised = sanitised[:255]

    if not sanitised:
        raise FridayValidationError(
            message="Filename is empty after sanitisation",
            error_code="VALIDATION_FILENAME_SANITISED_EMPTY",
            details={"original": filename},
        )

    return sanitised


def sanitize_input(text: str) -> str:
    """Apply basic input sanitisation.

    Strips leading/trailing whitespace, collapses internal whitespace runs,
    and truncates to :data:`_MAX_INPUT_LENGTH` characters.

    Args:
        text: Raw user input.

    Returns:
        The sanitised string.
    """
    if not isinstance(text, str):
        raise FridayValidationError(
            message=f"Input must be a string, got {type(text).__name__}",
            error_code="VALIDATION_INPUT_TYPE",
            details={"received_type": type(text).__name__},
        )

    sanitised = text.strip()
    # Collapse multiple whitespace characters into a single space
    sanitised = re.sub(r"\s+", " ", sanitised)
    # Truncate
    sanitised = sanitised[:_MAX_INPUT_LENGTH]
    return sanitised
