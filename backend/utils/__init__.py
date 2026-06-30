"""
FRIDAY OS — Utilities Package.

Re-exports every public symbol from the utils sub-modules so that
consumers can write concise imports::

    from backend.utils import get_logger, FridayError, generate_id
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
from backend.utils.logger import (
    LogContext,
    get_logger,
    log_context,
    setup_logging,
)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
from backend.utils.exceptions import (
    AgentError,
    AutomationError,
    BrowserError,
    ConfigurationError,
    DatabaseError,
    FileOperationError,
    FridayConnectionError,
    FridayError,
    FridaySecurityError,
    FridayValidationError,
    LLMError,
    RetryExhaustedError,
    TaskError,
    VoiceError,
)

# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------
from backend.utils.validators import (
    sanitize_filename,
    sanitize_input,
    validate_enum_value,
    validate_file_extension,
    validate_json_string,
    validate_not_empty,
    validate_path_safe,
    validate_port,
    validate_url,
)

# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------
from backend.utils.formatters import (
    format_agent_status,
    format_duration,
    format_error,
    format_file_size,
    format_log_entry,
    format_success,
    format_task_status,
    format_timestamp,
    truncate_text,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
from backend.utils.helpers import (
    calculate_hash,
    chunk_list,
    deep_merge,
    ensure_directory,
    generate_id,
    get_timestamp,
    measure_time,
    read_file_async,
    retry_async,
    safe_json_dumps,
    safe_json_loads,
    write_file_async,
)

__all__ = [
    # Logger
    "setup_logging",
    "get_logger",
    "LogContext",
    "log_context",
    # Exceptions
    "FridayError",
    "ConfigurationError",
    "DatabaseError",
    "FridayConnectionError",
    "FridayValidationError",
    "AgentError",
    "TaskError",
    "FridaySecurityError",
    "LLMError",
    "VoiceError",
    "AutomationError",
    "BrowserError",
    "FileOperationError",
    "RetryExhaustedError",
    # Validators
    "validate_not_empty",
    "validate_path_safe",
    "validate_url",
    "validate_port",
    "validate_enum_value",
    "validate_file_extension",
    "validate_json_string",
    "sanitize_filename",
    "sanitize_input",
    # Formatters
    "format_timestamp",
    "format_duration",
    "format_file_size",
    "format_error",
    "format_success",
    "format_task_status",
    "format_agent_status",
    "truncate_text",
    "format_log_entry",
    # Helpers
    "generate_id",
    "get_timestamp",
    "ensure_directory",
    "safe_json_loads",
    "safe_json_dumps",
    "read_file_async",
    "write_file_async",
    "calculate_hash",
    "retry_async",
    "chunk_list",
    "deep_merge",
    "measure_time",
]
