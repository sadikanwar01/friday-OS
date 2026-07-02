"""
FRIDAY OS - Tool Registry.

Manages the registration and retrieval of all automation tools.
Ensures the Engine does not have tight coupling to individual tools.
"""

from __future__ import annotations

from backend.automation.base import BaseTool
from backend.utils.exceptions import ConfigurationError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """Registry for dynamically managing automation tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a new tool instance."""
        if tool.name in self._tools:
            logger.warning("tool_already_registered", tool_name=tool.name)
            return

        self._tools[tool.name] = tool
        logger.debug("tool_registered", tool_name=tool.name, safety_level=tool.default_safety_level)

    def unregister(self, tool_name: str) -> None:
        """Remove a tool from the registry."""
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.debug("tool_unregistered", tool_name=tool_name)

    def get_tool(self, tool_name: str) -> BaseTool:
        """Retrieve a tool by name."""
        if tool_name not in self._tools:
            raise ConfigurationError(
                message=f"Tool '{tool_name}' is not registered.", error_code="TOOL_NOT_FOUND"
            )
        return self._tools[tool_name]

    def list_tools(self) -> list[dict[str, str]]:
        """List metadata for all registered tools, useful for the Planner."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "safety_level": tool.default_safety_level.value,
            }
            for tool in self._tools.values()
        ]
