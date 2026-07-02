"""
FRIDAY OS - Browser Automation Tool.

Provides headless and headful browser automation using Playwright.
"""

from __future__ import annotations

from typing import Any

from backend.automation.base import BaseTool, SafetyLevel, ToolResult
from backend.utils.exceptions import BrowserError


class BrowserTool(BaseTool):
    @property
    def name(self) -> str:
        return "browser"

    @property
    def description(self) -> str:
        return "Navigates websites, clicks elements, and extracts text."

    @property
    def default_safety_level(self) -> SafetyLevel:
        return SafetyLevel.SAFE

    async def execute(self, action: str, **kwargs: Any) -> ToolResult:
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                try:
                    browser = await p.chromium.launch(headless=kwargs.get("headless", True))
                except Exception as launch_exc:
                    if "Executable doesn't exist" in str(launch_exc):
                        raise BrowserError(
                            message="Browser binaries missing. Please run `playwright install chromium`.",
                            error_code="MISSING_BINARIES",
                        ) from launch_exc
                    raise

                page = await browser.new_page()

                try:
                    if action == "goto":
                        url = kwargs.get("url")
                        if not url:
                            return ToolResult(success=False, error="Missing URL.")
                        await page.goto(url)
                        title = await page.title()
                        return ToolResult(
                            success=True, output=f"Navigated to {url}. Title: {title}"
                        )

                    elif action == "extract_text":
                        url = kwargs.get("url")
                        if url:
                            await page.goto(url)
                        text = await page.evaluate("document.body.innerText")
                        return ToolResult(success=True, output=text)

                    elif action == "screenshot":
                        path = kwargs.get("path", "browser_screenshot.png")
                        url = kwargs.get("url")
                        if url:
                            await page.goto(url)
                        await page.screenshot(path=path)
                        return ToolResult(success=True, output=f"Screenshot saved to {path}")

                    else:
                        return ToolResult(success=False, error=f"Unknown browser action: {action}")
                finally:
                    await browser.close()

        except Exception as exc:
            return ToolResult(success=False, error=f"BrowserTool Error: {exc}")
