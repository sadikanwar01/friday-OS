"""Tests for the Automation Engine."""

import pytest

from backend.automation.base import BaseTool, SafetyLevel, ToolResult
from backend.automation.engine import AutomationEngine
from backend.automation.registry import ToolRegistry
from backend.automation.safety import PermissionManager, SafetyLayer
from backend.utils.exceptions import ConfigurationError, FridaySecurityError


class MockSafeTool(BaseTool):
    @property
    def name(self) -> str:
        return "mock_safe"

    @property
    def description(self) -> str:
        return "A safe mock tool."

    @property
    def default_safety_level(self) -> SafetyLevel:
        return SafetyLevel.SAFE

    async def execute(self, action: str, **kwargs) -> ToolResult:
        return ToolResult(success=True, output="Mock safe executed.")


@pytest.fixture
def engine():
    registry = ToolRegistry()
    registry.register(MockSafeTool())

    pm = PermissionManager()
    # auto mode allows SAFE things to pass without confirmation
    safety = SafetyLayer(permission_manager=pm, default_mode="auto")

    return AutomationEngine(registry=registry, safety_layer=safety)


@pytest.mark.asyncio
async def test_engine_successful_execution(engine):
    """Test successful execution of a registered tool."""
    result = await engine.execute_tool("mock_safe", "do_something")
    assert result.success is True
    assert result.output == "Mock safe executed."


@pytest.mark.asyncio
async def test_engine_unregistered_tool(engine):
    """Test executing a non-existent tool raises ConfigurationError."""
    with pytest.raises(ConfigurationError) as exc:
        await engine.execute_tool("not_real_tool", "action")
    assert exc.value.error_code == "TOOL_NOT_FOUND"


@pytest.mark.asyncio
async def test_engine_blocked_by_safety(engine):
    """Test that the engine properly defers to safety layer and raises."""
    # We pass a kwarg that matches a BLOCKED regex to trigger the safety layer
    with pytest.raises(FridaySecurityError) as exc:
        await engine.execute_tool("mock_safe", "do_something", command="rm -rf /")
    assert exc.value.error_code == "ACTION_BLOCKED"
