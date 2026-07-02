"""
FRIDAY OS — General-Purpose Helper Functions.

A collection of commonly needed utilities: unique-ID generation, timestamps,
async file I/O, JSON helpers (backed by ``orjson``), hashing, retry logic,
collection manipulation, and timing.

Usage::

    from backend.utils.helpers import generate_id, safe_json_dumps, retry_async

    uid = generate_id()
    payload = safe_json_dumps({"key": "value"}, pretty=True)
"""

from __future__ import annotations

import asyncio
import hashlib
import time
import uuid
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

import aiofiles  # type: ignore
import orjson

from backend.utils.exceptions import FileOperationError, RetryExhaustedError

T = TypeVar("T")


# ---------------------------------------------------------------------------
# ID / Timestamp
# ---------------------------------------------------------------------------


def generate_id() -> str:
    """Generate a random UUID4 string.

    Returns:
        A lowercase UUID4 string (e.g. ``"a3f1b2c4-..."``)
    """
    return str(uuid.uuid4())


def get_timestamp() -> datetime:
    """Return the current UTC timestamp as a timezone-aware datetime.

    Returns:
        :class:`~datetime.datetime` with ``tzinfo=timezone.utc``.
    """
    return datetime.now(tz=UTC)


# ---------------------------------------------------------------------------
# Filesystem
# ---------------------------------------------------------------------------


def ensure_directory(path: Path) -> Path:
    """Create *path* (and parents) if it does not already exist.

    Args:
        path: Directory path to ensure.

    Returns:
        The same *path* after creation.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


async def read_file_async(path: Path) -> str:
    """Read the entire contents of a text file asynchronously.

    Args:
        path: Path to the file.

    Returns:
        The file contents as a string.

    Raises:
        FileOperationError: If the file cannot be read.
    """
    try:
        async with aiofiles.open(path, encoding="utf-8") as fh:
            return await fh.read()
    except FileNotFoundError as exc:
        raise FileOperationError(
            message=f"File not found: {path}",
            error_code="FILE_NOT_FOUND",
            path=str(path),
        ) from exc
    except PermissionError as exc:
        raise FileOperationError(
            message=f"Permission denied: {path}",
            error_code="FILE_PERMISSION",
            path=str(path),
        ) from exc
    except OSError as exc:
        raise FileOperationError(
            message=f"Failed to read file: {path} ({exc})",
            error_code="FILE_READ_ERROR",
            path=str(path),
        ) from exc


async def write_file_async(path: Path, content: str) -> None:
    """Write *content* to a text file asynchronously.

    Parent directories are created automatically.

    Args:
        path: Destination file path.
        content: String content to write.

    Raises:
        FileOperationError: If the file cannot be written.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, mode="w", encoding="utf-8") as fh:
            await fh.write(content)
    except PermissionError as exc:
        raise FileOperationError(
            message=f"Permission denied: {path}",
            error_code="FILE_PERMISSION",
            path=str(path),
        ) from exc
    except OSError as exc:
        raise FileOperationError(
            message=f"Failed to write file: {path} ({exc})",
            error_code="FILE_WRITE_ERROR",
            path=str(path),
        ) from exc


# ---------------------------------------------------------------------------
# JSON helpers (orjson-backed)
# ---------------------------------------------------------------------------


def safe_json_loads(text: str, default: Any = None) -> Any:
    """Parse a JSON string, returning *default* on failure.

    Uses :mod:`orjson` for speed.

    Args:
        text: JSON-encoded string.
        default: Fallback value returned if parsing fails.

    Returns:
        The parsed Python object, or *default*.
    """
    try:
        return orjson.loads(text)
    except (orjson.JSONDecodeError, TypeError, ValueError):
        return default


def safe_json_dumps(data: Any, pretty: bool = False) -> str:
    """Serialise *data* to a JSON string, with optional pretty-printing.

    Uses :mod:`orjson` for speed.  Falls back to ``str(data)`` if
    serialisation fails.

    Args:
        data: The object to serialise.
        pretty: If ``True`` the output is indented for readability.

    Returns:
        A JSON string.
    """
    try:
        opts = orjson.OPT_NON_STR_KEYS
        if pretty:
            opts |= orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS
        return orjson.dumps(data, option=opts).decode("utf-8")
    except (TypeError, orjson.JSONEncodeError):
        return str(data)


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------


def calculate_hash(content: str) -> str:
    """Compute the SHA-256 hex digest of *content*.

    Args:
        content: UTF-8 string to hash.

    Returns:
        A 64-character lowercase hex string.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Retry
# ---------------------------------------------------------------------------


async def retry_async(
    func: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    **kwargs: Any,
) -> Any:
    """Invoke an async callable with exponential-backoff retry.

    Args:
        func: The async callable to execute.
        *args: Positional arguments forwarded to *func*.
        max_retries: Maximum number of retry attempts.
        delay: Initial delay (seconds) between retries.
        backoff: Multiplicative backoff factor applied after each retry.
        **kwargs: Keyword arguments forwarded to *func*.

    Returns:
        The return value of *func* on success.

    Raises:
        RetryExhaustedError: If all retry attempts fail.
    """
    last_error: BaseException | None = None
    current_delay = delay

    for attempt in range(1, max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                await asyncio.sleep(current_delay)
                current_delay *= backoff

    raise RetryExhaustedError(
        message=f"All {max_retries} retries exhausted for {getattr(func, '__name__', repr(func))}",
        error_code="RETRY_EXHAUSTED",
        details={"last_error": str(last_error)},
        attempts=max_retries,
    )


# ---------------------------------------------------------------------------
# Collection utilities
# ---------------------------------------------------------------------------


def chunk_list(lst: list[Any], chunk_size: int) -> list[list[Any]]:
    """Split *lst* into sub-lists of at most *chunk_size* elements.

    Args:
        lst: The list to chunk.
        chunk_size: Maximum size of each chunk (must be ≥ 1).

    Returns:
        A list of sub-lists.

    Raises:
        ValueError: If *chunk_size* is less than 1.
    """
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base*.

    Nested dicts are merged; all other types in *override* replace the
    corresponding key in *base*.  Neither input dict is mutated.

    Args:
        base: The base dictionary.
        override: The overriding dictionary.

    Returns:
        A new merged dictionary.
    """
    merged: dict[str, Any] = {**base}
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------


@asynccontextmanager
async def measure_time() -> AsyncGenerator[dict[str, float], None]:
    """Async context manager that measures wall-clock execution time.

    The elapsed time (in seconds) is stored in the yielded dict under the
    key ``"elapsed"``.  It is also available as ``"elapsed_ms"`` in
    milliseconds.

    Usage::

        async with measure_time() as timing:
            await some_operation()
        print(f"Took {timing['elapsed']:.3f}s")

    Yields:
        A mutable dict that is populated with ``elapsed`` and
        ``elapsed_ms`` after the block completes.
    """
    result: dict[str, float] = {"elapsed": 0.0, "elapsed_ms": 0.0}
    start = time.perf_counter()
    try:
        yield result
    finally:
        elapsed = time.perf_counter() - start
        result["elapsed"] = round(elapsed, 6)
        result["elapsed_ms"] = round(elapsed * 1000, 3)
