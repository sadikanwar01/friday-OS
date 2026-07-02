"""
FRIDAY OS - Terminal Tool.
"""

from __future__ import annotations

import asyncio
from typing import Any

from backend.automation.base import BaseTool, SafetyLevel, ToolResult


class TerminalTool(BaseTool):
    @property
    def name(self) -> str:
        return "terminal"

    @property
    def description(self) -> str:
        return "Executes shell commands in the background."

    @property
    def default_safety_level(self) -> SafetyLevel:
        return SafetyLevel.CONFIRM

    async def execute(self, action: str, **kwargs: Any) -> ToolResult:
        if action != "run_command":
            return ToolResult(success=False, error=f"Unknown terminal action: {action}")

        command = kwargs.get("command")
        if not command:
            return ToolResult(success=False, error="Missing required parameter: 'command'")

        cwd = kwargs.get("cwd")
        timeout = kwargs.get("timeout", 30)

        try:
            process = await asyncio.create_subprocess_shell(
                command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except TimeoutError:
                process.kill()
                return ToolResult(
                    success=False, error=f"Command timed out after {timeout} seconds."
                )

            output = stdout.decode().strip()
            error = stderr.decode().strip()

            success = process.returncode == 0

            full_output = []
            if output:
                full_output.append(output)
            if error:
                full_output.append(f"STDERR: {error}")

            return ToolResult(
                success=success,
                output="\n".join(full_output)
                if full_output
                else "Command executed successfully (no output).",
                data={"returncode": process.returncode},
            )

        except Exception as exc:
            return ToolResult(success=False, error=f"TerminalTool Error: {exc}")
