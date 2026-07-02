"""
FRIDAY OS - Tool Interface (Phase 2A Architecture).

Defines the abstract base class for tools that the LLM can execute.
Future modules (Browser, Code Execution, File Management) will inherit from this.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class for all callable tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The exact name the LLM uses to invoke this tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A detailed description of what the tool does and when to use it."""
        pass

    @property
    @abstractmethod
    def parameters_schema(self) -> dict[str, Any]:
        """JSON Schema defining the expected parameters for this tool.

        Example:
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str | dict[str, Any]:
        """Execute the tool with the given parameters and return the result.

        Args:
            **kwargs: The parameters parsed from the LLM's request.

        Returns:
            A string or a JSON-serializable dictionary containing the execution result.
        """
        pass
