"""
FRIDAY OS — Output Formatting Utilities.

Pure functions that produce standardised string and dict representations
used across the API, CLI, and logging subsystems.

Usage::

    from backend.utils.formatters import format_timestamp, format_file_size

    ts = format_timestamp()
    size = format_file_size(1_500_000)  # "1.43 MB"
"""

from __future__ import annotations

import traceback
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Timestamp / Duration / Size
# ---------------------------------------------------------------------------

def format_timestamp(dt: datetime | None = None) -> str:
    """Return an ISO-8601 formatted timestamp string.

    If *dt* is ``None`` the current UTC time is used.

    Args:
        dt: Optional :class:`~datetime.datetime` instance.

    Returns:
        An ISO-8601 string (e.g. ``"2026-06-29T20:30:00+00:00"``).
    """
    if dt is None:
        dt = datetime.now(tz=timezone.utc)
    return dt.isoformat()


def format_duration(seconds: float) -> str:
    """Convert *seconds* to a human-readable duration string.

    Examples::

        format_duration(0.5)    # "0.50s"
        format_duration(90)     # "1m 30s"
        format_duration(3661)   # "1h 1m 1s"
        format_duration(90061)  # "1d 1h 1m 1s"

    Args:
        seconds: Duration in seconds (may be fractional).

    Returns:
        A human-friendly duration string.
    """
    if seconds < 0:
        return f"-{format_duration(-seconds)}"

    if seconds < 60:
        return f"{seconds:.2f}s"

    total_seconds = int(seconds)
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)

    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def format_file_size(size_bytes: int) -> str:
    """Convert *size_bytes* to a human-readable file-size string.

    Uses binary prefixes (KiB-style values but labelled KB/MB/GB/TB for
    readability), consistent with most desktop OS conventions.

    Args:
        size_bytes: File size in bytes.

    Returns:
        A human-friendly size string (e.g. ``"1.50 MB"``).
    """
    if size_bytes < 0:
        return f"-{format_file_size(-size_bytes)}"

    units = ("B", "KB", "MB", "GB", "TB", "PB")
    size = float(size_bytes)
    for unit in units[:-1]:
        if abs(size) < 1024.0:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} {units[-1]}"


# ---------------------------------------------------------------------------
# API response helpers
# ---------------------------------------------------------------------------

def format_error(error: Exception) -> dict[str, Any]:
    """Build a standardised error-response dictionary from an exception.

    If the exception exposes a ``to_dict()`` method (i.e.
    :class:`~backend.utils.exceptions.FridayError`), it is used.  Otherwise
    a generic representation is constructed.

    Args:
        error: The exception instance.

    Returns:
        A dict with ``status``, ``error`` (nested), and ``traceback``.
    """
    # Use to_dict() when available (FridayError hierarchy)
    if hasattr(error, "to_dict") and callable(error.to_dict):
        error_data: dict[str, Any] = error.to_dict()
    else:
        error_data = {
            "error_type": type(error).__name__,
            "message": str(error),
        }

    return {
        "status": "error",
        "error": error_data,
        "traceback": traceback.format_exception(type(error), error, error.__traceback__),
    }


def format_success(data: Any = None, message: str = "Success") -> dict[str, Any]:
    """Build a standardised success-response dictionary.

    Args:
        data: Payload to include in the response.
        message: Human-readable success message.

    Returns:
        A dict with ``status``, ``message``, and ``data``.
    """
    return {
        "status": "success",
        "message": message,
        "data": data,
    }


# ---------------------------------------------------------------------------
# Status helpers
# ---------------------------------------------------------------------------

def format_task_status(status: str, progress: float = 0.0) -> dict[str, Any]:
    """Build a task-status response dictionary.

    Args:
        status: Current task status (e.g. ``"running"``, ``"completed"``).
        progress: Completion percentage as a float in ``[0.0, 100.0]``.

    Returns:
        A dict describing the task's status.
    """
    clamped_progress = max(0.0, min(100.0, progress))
    return {
        "status": status,
        "progress": round(clamped_progress, 2),
        "timestamp": format_timestamp(),
    }


def format_agent_status(
    agent_name: str,
    status: str,
    current_task: str | None = None,
) -> dict[str, Any]:
    """Build an agent-status response dictionary.

    Args:
        agent_name: Name of the agent.
        status: Current agent status (e.g. ``"idle"``, ``"executing"``).
        current_task: Optional description of the task being executed.

    Returns:
        A dict describing the agent's status.
    """
    result: dict[str, Any] = {
        "agent_name": agent_name,
        "status": status,
        "timestamp": format_timestamp(),
    }
    if current_task is not None:
        result["current_task"] = current_task
    return result


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def truncate_text(
    text: str,
    max_length: int = 200,
    suffix: str = "...",
) -> str:
    """Truncate *text* to *max_length* characters, appending *suffix*.

    If the text is already within the limit it is returned unchanged.

    Args:
        text: The text to truncate.
        max_length: Maximum character count (including suffix).
        suffix: The truncation indicator appended to shortened text.

    Returns:
        The (possibly truncated) string.
    """
    if len(text) <= max_length:
        return text
    truncated_length = max_length - len(suffix)
    if truncated_length <= 0:
        return suffix[:max_length]
    return text[:truncated_length] + suffix


# ---------------------------------------------------------------------------
# Log entry formatting
# ---------------------------------------------------------------------------

def format_log_entry(
    level: str,
    message: str,
    context: dict[str, Any] | None = None,
) -> str:
    """Format a single log line for plain-text output.

    Produces a string like::

        [2026-06-29T20:30:00+00:00] [INFO] Server started | port=8000

    Args:
        level: Log level (e.g. ``"INFO"``).
        message: Log message body.
        context: Optional dict of contextual key-value pairs.

    Returns:
        A formatted log-line string.
    """
    ts = format_timestamp()
    line = f"[{ts}] [{level.upper()}] {message}"
    if context:
        ctx_parts = " | ".join(f"{k}={v}" for k, v in context.items())
        line += f" | {ctx_parts}"
    return line
