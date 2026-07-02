"""
FRIDAY OS - Automation Engine Abstract Interfaces.

Defines the contract for all automation tools, safety levels,
and execution results.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any


class SafetyLevel(StrEnum):
    """Defines the danger/safety level of a tool or specific action."""

    SAFE = "safe"  # Completely safe (read-only, no side effects)
    CONFIRM = "confirm"  # Requires confirmation in secure mode (minor side effects)
    RESTRICTED = "restricted"  # Requires confirmation always (destructive or system-level)
    BLOCKED = "blocked"  # Never allowed by the engine


class ToolResult:
    """Standardized output from any automation tool."""

    def __init__(
        self,
        success: bool,
        output: str | None = None,
        error: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.success = success
        self.output = output
        self.error = error
        self.data = data or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "data": self.data,
        }


class BaseTool(ABC):
    """Abstract base class for all automation tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the tool (e.g., 'terminal', 'browser')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A description of what the tool does, used by the Planner."""
        pass

    @property
    @abstractmethod
    def default_safety_level(self) -> SafetyLevel:
        """The baseline safety level for the tool."""
        pass

    @abstractmethod
    async def execute(self, action: str, **kwargs: Any) -> ToolResult:
        """Execute a specific action using this tool.

        Args:
            action: The specific command or action the tool should perform.
            **kwargs: Additional parameters required by the action.

        Returns:
            A ToolResult containing the success status and output.
        """
        pass
