"""
FRIDAY OS - File System Tool.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from backend.automation.base import BaseTool, SafetyLevel, ToolResult


class FileSystemTool(BaseTool):
    @property
    def name(self) -> str:
        return "filesystem"

    @property
    def description(self) -> str:
        return "Reads, writes, and manages local files and directories."

    @property
    def default_safety_level(self) -> SafetyLevel:
        # FS is safe for reading, but the Engine/SafetyLayer elevates write/delete to RESTRICTED/CONFIRM
        return SafetyLevel.SAFE

    async def execute(self, action: str, **kwargs: Any) -> ToolResult:
        path = kwargs.get("path")
        if not path:
            return ToolResult(success=False, error="Missing required parameter: 'path'")

        target_path = Path(path).resolve()

        try:
            if action == "read_file":
                if not target_path.is_file():
                    return ToolResult(success=False, error=f"File not found: {target_path}")
                content = target_path.read_text(encoding="utf-8")
                return ToolResult(success=True, output=content)

            elif action == "write_file":
                content = kwargs.get("content", "")
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(content, encoding="utf-8")
                return ToolResult(success=True, output=f"Successfully wrote to {target_path}")

            elif action == "delete_file":
                if not target_path.exists():
                    return ToolResult(success=False, error=f"File not found: {target_path}")
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()
                return ToolResult(success=True, output=f"Successfully deleted {target_path}")

            elif action == "list_dir":
                if not target_path.is_dir():
                    return ToolResult(success=False, error=f"Directory not found: {target_path}")
                items = os.listdir(target_path)
                return ToolResult(success=True, output="\n".join(items), data={"items": items})

            else:
                return ToolResult(success=False, error=f"Unknown filesystem action: {action}")

        except Exception as exc:
            return ToolResult(success=False, error=f"FileSystemTool Error: {exc}")
