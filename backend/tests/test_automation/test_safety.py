"""Tests for the Automation Safety Layer."""

import pytest

from backend.automation.base import SafetyLevel
from backend.automation.safety import PermissionManager, SafetyLayer
from backend.utils.exceptions import FridaySecurityError


@pytest.fixture
def safety_layer():
    pm = PermissionManager()
    # Use "safe" default mode so we test strict confirmation
    return SafetyLayer(permission_manager=pm, default_mode="safe")


def test_safety_evaluate_blocked(safety_layer):
    """Test that blocked patterns evaluate to BLOCKED."""
    level = safety_layer.evaluate_action(
        tool_name="terminal",
        tool_safety_level=SafetyLevel.CONFIRM,
        action="run_command",
        command="rm -rf /",
    )
    assert level == SafetyLevel.BLOCKED

    # Another blocked
    level2 = safety_layer.evaluate_action(
        tool_name="terminal",
        tool_safety_level=SafetyLevel.CONFIRM,
        action="run_command",
        command="del /f /s /q C:\\",
    )
    assert level2 == SafetyLevel.BLOCKED


def test_safety_evaluate_restricted(safety_layer):
    """Test that dangerous patterns evaluate to RESTRICTED."""
    level = safety_layer.evaluate_action(
        tool_name="terminal",
        tool_safety_level=SafetyLevel.SAFE,
        action="run_command",
        command="chmod 777 /etc",
    )
    assert level == SafetyLevel.RESTRICTED


def test_safety_evaluate_safe_mode(safety_layer):
    """Test that in 'safe' mode, SAFE tools become CONFIRM if not strictly safe."""
    level = safety_layer.evaluate_action(
        tool_name="mouse",
        tool_safety_level=SafetyLevel.CONFIRM,  # Mouse defaults to confirm
        action="click",
    )
    # Because mode='safe', and tool is CONFIRM, it stays CONFIRM
    assert level == SafetyLevel.CONFIRM


def test_safety_validate_or_raise_blocked(safety_layer):
    """Test that BLOCKED raises exception."""
    with pytest.raises(FridaySecurityError) as exc:
        safety_layer.validate_or_raise(
            tool_name="terminal",
            tool_safety_level=SafetyLevel.CONFIRM,
            action="run_command",
            command="rm -rf /",
        )
    assert exc.value.error_code == "ACTION_BLOCKED"


def test_safety_validate_or_raise_unapproved_restricted(safety_layer):
    """Test that unapproved restricted raises exception."""
    with pytest.raises(FridaySecurityError) as exc:
        safety_layer.validate_or_raise(
            tool_name="terminal",
            tool_safety_level=SafetyLevel.CONFIRM,
            action="run_command",
            command="shutdown now",
        )
    assert exc.value.error_code == "CONFIRMATION_REQUIRED"


def test_safety_validate_or_raise_approved(safety_layer):
    """Test that approved actions bypass the security error."""
    tool_name = "terminal"
    action = "run_command"
    kwargs = {"command": "shutdown now"}

    # Approve it
    safety_layer.permission_manager.approve_action(tool_name, action, kwargs)

    # Should not raise
    safety_layer.validate_or_raise(
        tool_name=tool_name, tool_safety_level=SafetyLevel.CONFIRM, action=action, **kwargs
    )
