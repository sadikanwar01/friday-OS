"""
FRIDAY OS — Exception Hierarchy.

Every exception raised intentionally by FRIDAY OS inherits from
:class:`FridayError`.  Each subclass carries structured metadata
(``error_code``, ``details``, and domain-specific fields) and can be
serialised to a dict with :meth:`FridayError.to_dict` for API responses.

Usage::

    from backend.utils.exceptions import FridayValidationError

    raise FridayValidationError(
        message="Port out of range",
        error_code="VALIDATION_PORT",
        details={"port": 99999},
    )
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Base exception
# ---------------------------------------------------------------------------

class FridayError(Exception):
    """Base exception for all FRIDAY OS errors.

    Attributes:
        message:  Human-readable error description.
        error_code:  Machine-readable error code (e.g. ``"CONFIG_MISSING"``).
        details:  Optional dict with additional context.
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        error_code: str = "FRIDAY_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    # -- Serialisation -------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise the exception to a JSON-friendly dictionary.

        Returns:
            A dict containing ``error_type``, ``error_code``, ``message``,
            and ``details``.
        """
        return {
            "error_type": type(self).__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }

    # -- String representations ----------------------------------------------

    def __str__(self) -> str:
        base = f"[{self.error_code}] {self.message}"
        if self.details:
            base += f" | details={self.details}"
        return base

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"details={self.details!r})"
        )


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class ConfigurationError(FridayError):
    """Raised when loading or validating configuration fails.

    Examples include missing required keys, invalid value types, or
    inaccessible configuration files.
    """

    def __init__(
        self,
        message: str = "Configuration error",
        error_code: str = "CONFIG_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, details=details)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

class DatabaseError(FridayError):
    """Raised when a database operation fails.

    Covers query errors, migration issues, and integrity constraint
    violations.
    """

    def __init__(
        self,
        message: str = "Database error",
        error_code: str = "DB_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, details=details)


class FridayConnectionError(FridayError):
    """Raised when a connection to a database or external API fails.

    Named ``FridayConnectionError`` to avoid shadowing the built-in
    :class:`ConnectionError`.
    """

    def __init__(
        self,
        message: str = "Connection error",
        error_code: str = "CONNECTION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, details=details)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class FridayValidationError(FridayError):
    """Raised when input validation fails.

    Named ``FridayValidationError`` to avoid clashing with Pydantic's
    :class:`pydantic.ValidationError`.
    """

    def __init__(
        self,
        message: str = "Validation error",
        error_code: str = "VALIDATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, details=details)


# ---------------------------------------------------------------------------
# Agent / Task
# ---------------------------------------------------------------------------

class AgentError(FridayError):
    """Raised when an agent encounters an execution error.

    Attributes:
        agent_name: Identifier of the failing agent.
    """

    def __init__(
        self,
        message: str = "Agent error",
        error_code: str = "AGENT_ERROR",
        details: dict[str, Any] | None = None,
        *,
        agent_name: str = "unknown",
    ) -> None:
        self.agent_name = agent_name
        merged_details = {"agent_name": agent_name, **(details or {})}
        super().__init__(message=message, error_code=error_code, details=merged_details)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dict including ``agent_name``."""
        data = super().to_dict()
        data["agent_name"] = self.agent_name
        return data

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"agent_name={self.agent_name!r}, "
            f"details={self.details!r})"
        )


class TaskError(FridayError):
    """Raised when a task pipeline operation fails.

    Attributes:
        task_id: Identifier of the failing task.
    """

    def __init__(
        self,
        message: str = "Task error",
        error_code: str = "TASK_ERROR",
        details: dict[str, Any] | None = None,
        *,
        task_id: str = "unknown",
    ) -> None:
        self.task_id = task_id
        merged_details = {"task_id": task_id, **(details or {})}
        super().__init__(message=message, error_code=error_code, details=merged_details)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dict including ``task_id``."""
        data = super().to_dict()
        data["task_id"] = self.task_id
        return data

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"task_id={self.task_id!r}, "
            f"details={self.details!r})"
        )


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

class FridaySecurityError(FridayError):
    """Raised when a security policy is violated.

    Named ``FridaySecurityError`` to avoid shadowing potential stdlib
    extensions.

    Attributes:
        action: The action that was attempted.
        mode: The security mode active at the time (e.g. ``"strict"``).
    """

    def __init__(
        self,
        message: str = "Security violation",
        error_code: str = "SECURITY_ERROR",
        details: dict[str, Any] | None = None,
        *,
        action: str = "unknown",
        mode: str = "unknown",
    ) -> None:
        self.action = action
        self.mode = mode
        merged_details = {"action": action, "mode": mode, **(details or {})}
        super().__init__(message=message, error_code=error_code, details=merged_details)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dict including ``action`` and ``mode``."""
        data = super().to_dict()
        data["action"] = self.action
        data["mode"] = self.mode
        return data

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"action={self.action!r}, "
            f"mode={self.mode!r}, "
            f"details={self.details!r})"
        )


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

class LLMError(FridayError):
    """Raised when an LLM provider returns an error.

    Attributes:
        model: Name or identifier of the LLM model involved.
    """

    def __init__(
        self,
        message: str = "LLM error",
        error_code: str = "LLM_ERROR",
        details: dict[str, Any] | None = None,
        *,
        model: str = "unknown",
    ) -> None:
        self.model = model
        merged_details = {"model": model, **(details or {})}
        super().__init__(message=message, error_code=error_code, details=merged_details)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dict including ``model``."""
        data = super().to_dict()
        data["model"] = self.model
        return data

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"model={self.model!r}, "
            f"details={self.details!r})"
        )


# ---------------------------------------------------------------------------
# Voice / Automation / Browser
# ---------------------------------------------------------------------------

class VoiceError(FridayError):
    """Raised when the voice subsystem (STT / TTS) encounters an error."""

    def __init__(
        self,
        message: str = "Voice system error",
        error_code: str = "VOICE_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, details=details)


class AutomationError(FridayError):
    """Raised when a computer-automation action fails (e.g. PyAutoGUI)."""

    def __init__(
        self,
        message: str = "Automation error",
        error_code: str = "AUTOMATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, details=details)


class BrowserError(FridayError):
    """Raised when browser automation (e.g. Playwright) fails."""

    def __init__(
        self,
        message: str = "Browser automation error",
        error_code: str = "BROWSER_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, details=details)


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------

class FileOperationError(FridayError):
    """Raised when a filesystem operation fails.

    Attributes:
        path: The filesystem path involved.
    """

    def __init__(
        self,
        message: str = "File operation error",
        error_code: str = "FILE_ERROR",
        details: dict[str, Any] | None = None,
        *,
        path: str = "",
    ) -> None:
        self.path = path
        merged_details = {"path": path, **(details or {})}
        super().__init__(message=message, error_code=error_code, details=merged_details)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dict including ``path``."""
        data = super().to_dict()
        data["path"] = self.path
        return data

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"path={self.path!r}, "
            f"details={self.details!r})"
        )


# ---------------------------------------------------------------------------
# Retry
# ---------------------------------------------------------------------------

class RetryExhaustedError(FridayError):
    """Raised when all retry attempts have been exhausted.

    Attributes:
        attempts: Number of attempts made before giving up.
    """

    def __init__(
        self,
        message: str = "All retries exhausted",
        error_code: str = "RETRY_EXHAUSTED",
        details: dict[str, Any] | None = None,
        *,
        attempts: int = 0,
    ) -> None:
        self.attempts = attempts
        merged_details = {"attempts": attempts, **(details or {})}
        super().__init__(message=message, error_code=error_code, details=merged_details)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dict including ``attempts``."""
        data = super().to_dict()
        data["attempts"] = self.attempts
        return data

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"attempts={self.attempts!r}, "
            f"details={self.details!r})"
        )
