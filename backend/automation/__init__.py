"""
FRIDAY OS - Desktop Automation Module (Phase 4).

Provides capabilities for safe, automated interaction with the file system,
terminal, browser, and desktop graphical interface.
"""

from __future__ import annotations

from backend.automation.base import BaseTool, SafetyLevel, ToolResult
from backend.automation.engine import AutomationEngine
from backend.automation.registry import ToolRegistry
from backend.automation.safety import PermissionManager, SafetyLayer

# Import built-in tools
from backend.automation.tools.browser import BrowserTool
from backend.automation.tools.clipboard import ClipboardTool
from backend.automation.tools.fs import FileSystemTool
from backend.automation.tools.gui import KeyboardTool, MouseTool, ScreenshotTool, WindowTool
from backend.automation.tools.terminal import TerminalTool

__all__ = [
    "AutomationEngine",
    "BaseTool",
    "BrowserTool",
    "ClipboardTool",
    "FileSystemTool",
    "KeyboardTool",
    "MouseTool",
    "PermissionManager",
    "SafetyLayer",
    "SafetyLevel",
    "ScreenshotTool",
    "TerminalTool",
    "ToolRegistry",
    "ToolResult",
    "WindowTool",
]
