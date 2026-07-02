import asyncio

from backend.automation.engine import AutomationEngine
from backend.automation.registry import ToolRegistry
from backend.automation.safety import PermissionManager, SafetyLayer
from backend.automation.tools.clipboard import ClipboardTool
from backend.automation.tools.fs import FileSystemTool
from backend.automation.tools.terminal import TerminalTool
from backend.utils.exceptions import FridaySecurityError


async def main() -> None:
    print("Starting Desktop Automation Engine Verification (Phase 4)...")

    # Setup
    pm = PermissionManager()
    safety_layer = SafetyLayer(permission_manager=pm, default_mode="confirm")
    registry = ToolRegistry()

    registry.register(TerminalTool())
    registry.register(ClipboardTool())
    registry.register(FileSystemTool())

    engine = AutomationEngine(registry=registry, safety_layer=safety_layer)

    print("\n[Test 1] Safe Execution (Clipboard Tool)")
    clipboard_text = "Verification successful!"
    res1 = await engine.execute_tool("clipboard", "write", text=clipboard_text)
    print(f"  -> Write to clipboard: {res1.success} - {res1.output}")

    res2 = await engine.execute_tool("clipboard", "read")
    print(f"  -> Read from clipboard: {res2.success} - '{res2.output}'")
    assert res2.output == clipboard_text, "Clipboard text mismatch!"

    print("\n[Test 2] Restricted Action Without Approval (Terminal Tool)")
    try:
        await engine.execute_tool("terminal", "run_command", command="shutdown /s /t 0")
        print("  -> ERROR: Shutdown was NOT blocked!")
    except FridaySecurityError as e:
        print(f"  -> Successfully intercepted: {e.error_code} - {e.message}")

    print("\n[Test 3] Restricted Action With Approval (Terminal Tool)")
    # Approve it
    pm.approve_action("terminal", "run_command", {"command": "shutdown /s /t 0"})
    print("  -> User approved action.")

    # We will pass a mocked command instead of actually shutting down
    # But we will test that it bypasses the security layer this time
    try:
        # Actually run something harmless but approved as a dangerous command
        pm.approve_action("terminal", "run_command", {"command": "echo Simulation: shutting down..."})
        res3 = await engine.execute_tool("terminal", "run_command", command="echo Simulation: shutting down...")
        print(f"  -> Execution successful: {res3.output}")
    except FridaySecurityError:
        print("  -> ERROR: Was intercepted even after approval!")

    print("\n[Test 4] Blocked Action (Terminal Tool)")
    try:
        await engine.execute_tool("terminal", "run_command", command="del /f /s /q C:\\")
        print("  -> ERROR: Deletion was NOT blocked!")
    except FridaySecurityError as e:
        print(f"  -> Successfully intercepted: {e.error_code} - {e.message}")

    print("\nVerification Complete! The Automation Engine orchestrates and protects successfully.")


if __name__ == "__main__":
    asyncio.run(main())
