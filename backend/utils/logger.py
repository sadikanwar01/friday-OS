"""
FRIDAY OS — Structured Logging System.

Production-grade logging built on ``structlog`` and Python's standard ``logging``.
Provides colored console output for development, JSON output for production,
and rotating file handlers to keep log volume under control.

Usage::

    from backend.utils.logger import setup_logging, get_logger

    setup_logging(log_level="DEBUG")
    log = get_logger("my_module")
    log.info("server_started", port=8000)
"""

from __future__ import annotations

import logging
import sys
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Generator

import structlog
from structlog.types import Processor


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_LOG_DIR = Path("data/logs")
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_BACKUP_COUNT = 5
_LOG_FORMAT = "%(message)s"

_VALID_LOG_LEVELS: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


# ---------------------------------------------------------------------------
# Shared processors
# ---------------------------------------------------------------------------

def _build_shared_processors() -> list[Processor]:
    """Return the shared structlog processor chain."""
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ],
        ),
        structlog.processors.EventRenamer("event"),
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def setup_logging(
    log_level: str = "INFO",
    log_dir: Path | None = None,
    json_output: bool = False,
) -> None:
    """Configure the global logging pipeline.

    This must be called **once** at application startup.  Subsequent calls
    will reconfigure the pipeline (useful for tests).

    Args:
        log_level: One of ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``,
            ``CRITICAL``.  Case-insensitive.
        log_dir: Directory for rotated log files.  Created automatically.
            Defaults to ``data/logs/``.
        json_output: If ``True`` render log lines as JSON (production).
            Otherwise render colored console output (development).
    """
    level_name = log_level.upper()
    if level_name not in _VALID_LOG_LEVELS:
        raise ValueError(
            f"Invalid log level '{log_level}'. "
            f"Valid levels: {', '.join(_VALID_LOG_LEVELS)}"
        )
    numeric_level: int = _VALID_LOG_LEVELS[level_name]

    # Ensure log directory exists
    resolved_log_dir = (log_dir or _DEFAULT_LOG_DIR).resolve()
    resolved_log_dir.mkdir(parents=True, exist_ok=True)

    # ---- stdlib root logger ------------------------------------------------
    root_logger = logging.getLogger()
    # Clear any existing handlers to allow re-configuration
    root_logger.handlers.clear()
    root_logger.setLevel(numeric_level)

    # Console handler -------------------------------------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root_logger.addHandler(console_handler)

    # Rotating file handler --------------------------------------------------
    log_file = resolved_log_dir / "friday.log"
    file_handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root_logger.addHandler(file_handler)

    # ---- structlog configuration -------------------------------------------
    shared_processors = _build_shared_processors()

    if json_output:
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        # Import colorama and initialise for Windows ANSI support
        try:
            import colorama  # noqa: F811
            colorama.just_fix_windows_console()
        except ImportError:
            pass
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Apply structlog formatter to all stdlib handlers so that they share
    # the same processor pipeline.
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger for the given *name*.

    The logger is backed by Python's standard ``logging`` module, so it
    participates in the handler / formatter pipeline set up by
    :func:`setup_logging`.

    Args:
        name: Logger name — typically ``__name__`` of the calling module.

    Returns:
        A structlog :class:`~structlog.stdlib.BoundLogger` instance.
    """
    return structlog.get_logger(name)


# ---------------------------------------------------------------------------
# LogContext — add fields for a block of code
# ---------------------------------------------------------------------------

class LogContext:
    """Context manager that binds extra fields to **all** structlog loggers
    within the block using :mod:`structlog.contextvars`.

    Usage::

        with LogContext(request_id="abc-123", user="tony"):
            log.info("processing")  # includes request_id and user

    The bound variables are automatically cleared when the block exits.

    Args:
        **fields: Arbitrary keyword arguments that will be merged into the
            structlog context for the duration of the block.
    """

    def __init__(self, **fields: Any) -> None:
        self._fields = fields
        self._token: Any | None = None

    def __enter__(self) -> LogContext:
        """Bind contextual fields."""
        self._token = structlog.contextvars.bind_contextvars(**self._fields)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any | None,
    ) -> None:
        """Remove the contextual fields that were added on entry."""
        structlog.contextvars.unbind_contextvars(*self._fields.keys())


@contextmanager
def log_context(**fields: Any) -> Generator[None, None, None]:
    """Functional wrapper around :class:`LogContext`.

    Usage::

        with log_context(request_id="abc-123"):
            log.info("processing")

    Args:
        **fields: Context fields to bind for the duration of the block.

    Yields:
        ``None``
    """
    with LogContext(**fields):
        yield
