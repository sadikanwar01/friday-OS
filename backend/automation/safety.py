"""
FRIDAY OS - Safety Layer & Permission Manager.

Evaluates the danger of an action before it's executed by a tool,
enforcing strict blocks on dangerous commands and requiring user
confirmation for restricted ones.
"""

from __future__ import annotations

import re
from typing import Any

from backend.automation.base import SafetyLevel
from backend.utils.exceptions import FridaySecurityError
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Regex patterns for identifying dangerous commands
_RESTRICTED_PATTERNS = [
    re.compile(r"\brm\s+-rf\b", re.IGNORECASE),
    re.compile(r"\bdel\s+/f\b", re.IGNORECASE),
    re.compile(r"\bformat\b", re.IGNORECASE),
    re.compile(r"\bshutdown\b", re.IGNORECASE),
    re.compile(r"\brestart\b", re.IGNORECASE),
    re.compile(r"\bkill\b", re.IGNORECASE),
    re.compile(r"\btaskkill\b", re.IGNORECASE),
    re.compile(r"\bregedit\b", re.IGNORECASE),
    re.compile(r"\bchmod\s+777\b", re.IGNORECASE),
    re.compile(r"\bchown\b", re.IGNORECASE),
]

_BLOCKED_PATTERNS = [
    re.compile(r"^\s*rm\s+-rf\s+/\s*$", re.IGNORECASE),  # rm -rf /
    re.compile(r"^\s*del\s+/f\s+/s\s+/q\s+[c-zC-Z]:\\\s*$", re.IGNORECASE),  # del C:\
    re.compile(r"^\s*mkfs\b", re.IGNORECASE),
]


class PermissionManager:
    """Manages explicit user confirmations for restricted actions."""

    def __init__(self) -> None:
        self._approved_actions: set[str] = set()

    def _generate_action_hash(self, tool_name: str, action: str, kwargs: dict[str, Any]) -> str:
        """Generate a deterministic hash for an action and its arguments."""
        # A simple string representation is sufficient for this scope
        return f"{tool_name}:{action}:{str(kwargs)}"

    def is_approved(self, tool_name: str, action: str, kwargs: dict[str, Any]) -> bool:
        """Check if an action has been explicitly approved by the user."""
        action_hash = self._generate_action_hash(tool_name, action, kwargs)
        return action_hash in self._approved_actions

    def approve_action(self, tool_name: str, action: str, kwargs: dict[str, Any]) -> None:
        """Record an explicit user approval for a specific action."""
        action_hash = self._generate_action_hash(tool_name, action, kwargs)
        self._approved_actions.add(action_hash)
        logger.info("action_approved", tool=tool_name, action=action)

    def revoke_approval(self, tool_name: str, action: str, kwargs: dict[str, Any]) -> None:
        """Remove a previously approved action."""
        action_hash = self._generate_action_hash(tool_name, action, kwargs)
        self._approved_actions.discard(action_hash)


class SafetyLayer:
    """Middleware that intercepts and evaluates tool executions."""

    def __init__(
        self, permission_manager: PermissionManager, default_mode: str = "confirm"
    ) -> None:
        self.permission_manager = permission_manager
        # Modes: "safe" (all write actions require confirm), "confirm" (restricted requires confirm), "auto" (dangerous allowed if not blocked)
        self.default_mode = default_mode

    def evaluate_action(
        self,
        tool_name: str,
        tool_safety_level: SafetyLevel,
        action: str,
        **kwargs: Any,
    ) -> SafetyLevel:
        """Determine the effective safety level of an action."""

        # 1. Check if the entire tool is BLOCKED
        if tool_safety_level == SafetyLevel.BLOCKED:
            return SafetyLevel.BLOCKED

        command_str = str(kwargs.get("command", "")) or str(kwargs.get("path", "")) or action

        # 2. Check strict BLOCKED patterns
        for pattern in _BLOCKED_PATTERNS:
            if pattern.search(command_str):
                logger.warning(
                    "blocked_pattern_matched", pattern=pattern.pattern, command=command_str
                )
                return SafetyLevel.BLOCKED

        # 3. Check RESTRICTED patterns
        effective_level = tool_safety_level
        for pattern in _RESTRICTED_PATTERNS:
            if pattern.search(command_str):
                effective_level = SafetyLevel.RESTRICTED
                break

        # 4. Apply system-wide mode constraints
        if self.default_mode == "safe" and effective_level == SafetyLevel.SAFE:
            # In 'safe' mode, almost everything requires confirmation unless strictly safe
            effective_level = SafetyLevel.CONFIRM

        return effective_level

    def validate_or_raise(
        self,
        tool_name: str,
        tool_safety_level: SafetyLevel,
        action: str,
        **kwargs: Any,
    ) -> None:
        """Validate the action. Raise FridaySecurityError if not permitted."""

        level = self.evaluate_action(tool_name, tool_safety_level, action, **kwargs)

        if level == SafetyLevel.BLOCKED:
            logger.error("execution_blocked", tool=tool_name, action=action)
            raise FridaySecurityError(
                action=action,
                mode=self.default_mode,
                message=f"Action '{action}' via '{tool_name}' is permanently blocked for system safety.",
                error_code="ACTION_BLOCKED",
            )

        if level in (SafetyLevel.RESTRICTED, SafetyLevel.CONFIRM) and not self.permission_manager.is_approved(tool_name, action, kwargs):
            logger.warning("user_confirmation_required", tool=tool_name, action=action, level=level)
            raise FridaySecurityError(
                action=action,
                mode=self.default_mode,
                message=f"Action '{action}' via '{tool_name}' requires explicit user confirmation.",
                error_code="CONFIRMATION_REQUIRED"
            )

        # Action is either SAFE or was explicitly approved
        logger.debug("action_validated", tool=tool_name, action=action, level=level)
