"""
FRIDAY OS - Clipboard Tool.
"""

from __future__ import annotations

import asyncio
from typing import Any

from backend.automation.base import BaseTool, SafetyLevel, ToolResult


class ClipboardTool(BaseTool):
    @property
    def name(self) -> str:
        return "clipboard"

    @property
    def description(self) -> str:
        return "Reads from and writes to the system clipboard."

    @property
    def default_safety_level(self) -> SafetyLevel:
        return SafetyLevel.SAFE

    async def execute(self, action: str, **kwargs: Any) -> ToolResult:
        try:
            # Pyperclip is blocking, so we run it in a thread
            import pyperclip  # type: ignore  # type: ignore

            if action == "read":
                content = await asyncio.to_thread(pyperclip.paste)
                return ToolResult(success=True, output=content)

            elif action == "write":
                text = kwargs.get("text")
                if text is None:
                    return ToolResult(success=False, error="Missing required parameter: 'text'")

                await asyncio.to_thread(pyperclip.copy, text)
                return ToolResult(success=True, output="Successfully copied to clipboard.")

            else:
                return ToolResult(success=False, error=f"Unknown clipboard action: {action}")

        except Exception as exc:
            return ToolResult(success=False, error=f"ClipboardTool Error: {exc}")
