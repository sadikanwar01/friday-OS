"""
FRIDAY OS - Automation Engine.

The central orchestrator for Desktop Automation. Manages the registry
and wraps all executions in the Safety Layer.
"""

from __future__ import annotations

from typing import Any

from backend.automation.base import ToolResult
from backend.automation.registry import ToolRegistry
from backend.automation.safety import SafetyLayer
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AutomationEngine:
    """Orchestrates secure execution of automation tools."""

    def __init__(self, registry: ToolRegistry, safety_layer: SafetyLayer) -> None:
        self.registry = registry
        self.safety_layer = safety_layer

    async def execute_tool(self, tool_name: str, action: str, **kwargs: Any) -> ToolResult:
        """Execute a tool action securely.

        Args:
            tool_name: The name of the registered tool to execute.
            action: The specific action the tool should perform.
            **kwargs: Arguments to pass to the tool.

        Returns:
            ToolResult containing the output or error.

        Raises:
            FridaySecurityError: If the action is blocked or requires confirmation.
        """
        logger.info("executing_automation_tool", tool=tool_name, action=action)

        # 1. Retrieve the Tool
        # This will raise ConfigurationError if not found
        tool = self.registry.get_tool(tool_name)

        # 2. Safety Validation
        # This will raise FridaySecurityError if blocked or requires unapproved confirmation
        self.safety_layer.validate_or_raise(
            tool_name=tool.name,
            tool_safety_level=tool.default_safety_level,
            action=action,
            **kwargs,
        )

        # 3. Execution
        try:
            result = await tool.execute(action, **kwargs)
            logger.debug("tool_execution_completed", success=result.success)
            return result
        except Exception as exc:
            logger.exception("tool_execution_failed_unexpectedly", exc=str(exc))
            return ToolResult(success=False, error=str(exc))
