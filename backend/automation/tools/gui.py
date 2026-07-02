"""
FRIDAY OS - GUI Tools.

Provides mouse, keyboard, window, and screenshot capabilities using
pyautogui, pygetwindow, and Pillow.
"""

from __future__ import annotations

import asyncio
from typing import Any

from backend.automation.base import BaseTool, SafetyLevel, ToolResult


class MouseTool(BaseTool):
    @property
    def name(self) -> str:
        return "mouse"

    @property
    def description(self) -> str:
        return "Controls the mouse cursor and clicks."

    @property
    def default_safety_level(self) -> SafetyLevel:
        return SafetyLevel.CONFIRM

    async def execute(self, action: str, **kwargs: Any) -> ToolResult:
        try:
            import pyautogui  # type: ignore  # type: ignore

            if action == "move":
                x = kwargs.get("x")
                y = kwargs.get("y")
                if x is None or y is None:
                    return ToolResult(success=False, error="Missing x or y coordinates.")
                await asyncio.to_thread(pyautogui.moveTo, x, y)
                return ToolResult(success=True, output=f"Moved mouse to ({x}, {y})")

            elif action == "click":
                button = kwargs.get("button", "left")
                await asyncio.to_thread(pyautogui.click, button=button)
                return ToolResult(success=True, output=f"Clicked {button} mouse button.")

            elif action == "scroll":
                clicks = kwargs.get("clicks", -10)  # negative is down
                await asyncio.to_thread(pyautogui.scroll, clicks)
                return ToolResult(success=True, output=f"Scrolled {clicks} clicks.")

            else:
                return ToolResult(success=False, error=f"Unknown mouse action: {action}")

        except Exception as exc:
            return ToolResult(success=False, error=f"MouseTool Error: {exc}")


class KeyboardTool(BaseTool):
    @property
    def name(self) -> str:
        return "keyboard"

    @property
    def description(self) -> str:
        return "Simulates keyboard typing and hotkeys."

    @property
    def default_safety_level(self) -> SafetyLevel:
        return SafetyLevel.CONFIRM

    async def execute(self, action: str, **kwargs: Any) -> ToolResult:
        try:
            import pyautogui

            if action == "type":
                text = kwargs.get("text")
                if not text:
                    return ToolResult(success=False, error="Missing text to type.")
                await asyncio.to_thread(pyautogui.write, text, interval=0.01)
                return ToolResult(success=True, output="Typed text successfully.")

            elif action == "press":
                key = kwargs.get("key")
                if not key:
                    return ToolResult(success=False, error="Missing key to press.")
                await asyncio.to_thread(pyautogui.press, key)
                return ToolResult(success=True, output=f"Pressed key: {key}")

            elif action == "hotkey":
                keys = kwargs.get("keys", [])
                if not keys:
                    return ToolResult(success=False, error="Missing keys for hotkey.")
                await asyncio.to_thread(pyautogui.hotkey, *keys)
                return ToolResult(success=True, output=f"Executed hotkey: {keys}")

            else:
                return ToolResult(success=False, error=f"Unknown keyboard action: {action}")

        except Exception as exc:
            return ToolResult(success=False, error=f"KeyboardTool Error: {exc}")


class WindowTool(BaseTool):
    @property
    def name(self) -> str:
        return "window"

    @property
    def description(self) -> str:
        return "Manages application windows."

    @property
    def default_safety_level(self) -> SafetyLevel:
        return SafetyLevel.SAFE

    async def execute(self, action: str, **kwargs: Any) -> ToolResult:
        try:
            import pygetwindow as gw  # type: ignore  # type: ignore

            if action == "list":
                titles = [w.title for w in gw.getAllWindows() if w.title]
                return ToolResult(success=True, output="\n".join(titles), data={"titles": titles})

            elif action == "focus":
                title = kwargs.get("title")
                if not title:
                    return ToolResult(success=False, error="Missing window title.")

                windows = gw.getWindowsWithTitle(title)
                if not windows:
                    return ToolResult(success=False, error=f"Window not found: {title}")

                win = windows[0]
                await asyncio.to_thread(win.activate)
                return ToolResult(success=True, output=f"Activated window: {win.title}")

            else:
                return ToolResult(success=False, error=f"Unknown window action: {action}")

        except Exception as exc:
            return ToolResult(success=False, error=f"WindowTool Error: {exc}")


class ScreenshotTool(BaseTool):
    @property
    def name(self) -> str:
        return "screenshot"

    @property
    def description(self) -> str:
        return "Captures a screenshot of the display."

    @property
    def default_safety_level(self) -> SafetyLevel:
        return SafetyLevel.SAFE

    async def execute(self, action: str, **kwargs: Any) -> ToolResult:
        if action != "capture":
            return ToolResult(success=False, error=f"Unknown screenshot action: {action}")

        try:
            import pyautogui

            save_path = kwargs.get("path")

            if save_path:
                await asyncio.to_thread(pyautogui.screenshot, save_path)
                return ToolResult(success=True, output=f"Screenshot saved to {save_path}")
            else:
                # If no path, we'd normally return the base64 or PIL image in data,
                # but for simplicity we'll just capture and return success.
                img = await asyncio.to_thread(pyautogui.screenshot)
                return ToolResult(success=True, output=f"Screenshot captured: {img.size}")

        except Exception as exc:
            return ToolResult(success=False, error=f"ScreenshotTool Error: {exc}")
