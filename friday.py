"""
FRIDAY OS - Entry Point (Integration Test)

Initializes all completed modules into a single runnable application.
"""

import asyncio
from pathlib import Path

from backend.automation.coordinator import ExecutionCoordinator
from backend.automation.engine import AutomationEngine
from backend.automation.registry import ToolRegistry
from backend.automation.safety import PermissionManager, SafetyLayer
from backend.automation.tools.browser import BrowserTool
from backend.automation.tools.clipboard import ClipboardTool
from backend.automation.tools.fs import FileSystemTool
from backend.automation.tools.gui import KeyboardTool, MouseTool, ScreenshotTool, WindowTool
from backend.automation.tools.terminal import TerminalTool
from backend.config import get_settings
from backend.database import async_session_factory, init_database
from backend.memory.manager import MemoryManager
from backend.planner.engine import PlanningEngine
from backend.utils.logger import get_logger, setup_logging
from backend.voice.pipeline import VoiceSessionManager


async def main() -> None:
    # 1. Initialize configuration & logging
    settings = get_settings()
    # Force push-to-talk for the test to avoid continuous listening
    settings.voice_mode = "push_to_talk"

    setup_logging(
        log_level=settings.app_log_level,
        log_dir=Path(settings.data_dir) / "logs",
        json_output=False
    )
    logger = get_logger("friday")
    logger.info("Starting FRIDAY OS...")

    # 2. Initialize database
    await init_database()
    logger.info("Database initialized.")

    # 3. Initialize providers (Router is lazy-loaded/global)

    # 4. Initialize memory
    session = async_session_factory()
    memory_manager = MemoryManager(session=session)
    logger.info("Memory initialized.")

    # 5. Initialize planner
    planner = PlanningEngine(memory_manager)
    logger.info("Planner initialized.")

    # 6. Initialize automation
    pm = PermissionManager()
    safety_layer = SafetyLayer(permission_manager=pm, default_mode="auto")
    registry = ToolRegistry()
    registry.register(TerminalTool())
    registry.register(FileSystemTool())
    registry.register(ClipboardTool())
    registry.register(MouseTool())
    registry.register(KeyboardTool())
    registry.register(WindowTool())
    registry.register(ScreenshotTool())
    registry.register(BrowserTool())

    automation_engine = AutomationEngine(registry=registry, safety_layer=safety_layer)
    execution_coordinator = ExecutionCoordinator(automation_engine=automation_engine)
    logger.info("Automation initialized.")

    # 7. Initialize voice
    voice = VoiceSessionManager(
        memory_manager=memory_manager,
        planning_engine=planner,
        execution_coordinator=execution_coordinator
    )
    await voice.initialize()
    logger.info("Voice initialized.")

    # 8. Start Interaction
    print("\n" + "="*50)
    print("FRIDAY OS is ready.")
    print("="*50)

    print("Voice mode: Text input (microphone not available)")
    print("Type your message and press Enter.")
    print("Type 'exit' or 'quit' to shut down.\n")

    import sys

    while True:
        try:
            sys.stdout.write("You > ")
            sys.stdout.flush()
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:  # EOF
                break
            user_input = line.strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            break

        response_text = None
        try:
            intent = await planner.intent_engine.detect_intent(user_input)

            if intent.requires_planning:
                plan = await planner.generate_plan(
                    user_id="default", user_input=user_input, intent=intent
                )

                if plan.goal:
                    response_text = await execution_coordinator.execute_plan(plan)
                else:
                    response_text = "I processed your request but no plan was generated."
            else:
                # Conversational route
                from backend.llm.router import provider_router
                gemini_model = settings.gemini_model or "gemini-2.5-flash"
                provider = provider_router.get_provider_for_model(gemini_model)
                response_text = await provider.generate(
                    model=gemini_model,
                    messages=[{"role": "user", "content": user_input}],
                    system_prompt="You are FRIDAY, a personal AI assistant. Be concise and helpful.",
                )

        except Exception as e:
            response_text = f"[Error] I couldn't process that request: {e}"

        print(f"\nFRIDAY > {response_text}\n")

    print("\nShutting down FRIDAY OS...")
    voice.stop()


if __name__ == "__main__":
    asyncio.run(main())
