import asyncio

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
from backend.voice.pipeline import VoiceSessionManager


async def run_integration_tests():
    print("========================================")
    print("FRIDAY OS RC1 - End-to-End Test Suite")
    print("========================================")

    settings = get_settings()
    settings.voice_mode = "push_to_talk"

    await init_database()
    session = async_session_factory()
    memory = MemoryManager(session=session)

    planner = PlanningEngine(memory)

    pm = PermissionManager()
    safety = SafetyLayer(permission_manager=pm, default_mode="auto")
    registry = ToolRegistry()
    registry.register(TerminalTool())
    registry.register(WindowTool())
    registry.register(MouseTool())
    registry.register(KeyboardTool())
    registry.register(ScreenshotTool())
    registry.register(ClipboardTool())
    registry.register(FileSystemTool())
    registry.register(BrowserTool())

    engine = AutomationEngine(registry, safety)
    coordinator = ExecutionCoordinator(engine)

    voice = VoiceSessionManager(memory, planner, coordinator)

    # Mock voice.initialize to bypass voice model checks for the test
    # (Since we are testing Planner -> Automation end-to-end here)
    async def mock_init():
        pass
    voice.initialize = mock_init
    await voice.initialize()

    # Mock Gemini provider for sandbox tests where a real key isn't present
    async def mock_generate(*args, **kwargs):
        import orjson

        # Create a dummy execution plan for the test to proceed to automation
        plan = {
            "plan_version": "1.0",
            "planner_version": "1.0.0",
            "goal": "Test goal",
            "steps": [],
            "required_tools": [],
            "required_memory": [],
            "dependencies": [],
            "risks": [],
            "confidence_score": 0.99,
            "confidence_reason": "Mocked",
            "verification_strategy": "None",
            "retry_strategy": "None",
            "expected_output": "Mocked output"
        }
        return orjson.dumps(plan).decode("utf-8")

    from backend.llm.providers.gemini import GeminiProvider
    GeminiProvider.generate = mock_generate

    scenarios = [
        "Hello Friday",
        "What is my name?",
        "Open Notepad",
        "Open Calculator",
        "Copy 'Hello World'",
        "Take Screenshot",
        "Open https://google.com",
        "Shutdown computer"
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[Test {i}/{len(scenarios)}] Injecting User Input: '{scenario}'")

        # Mock STT output
        async def mock_transcribe(*args, _scenario=scenario, **kwargs):
            return _scenario
        voice.stt.transcribe = mock_transcribe

        # Mock TTS output to capture FRIDAY's response
        async def mock_synthesize(text):
            print(f"  [FRIDAY Response] -> {text}")
            return b""
        voice.tts.synthesize = mock_synthesize

        # Mock Record
        async def mock_record(): return b"dummy_audio_that_is_long_enough_to_pass_the_length_check" * 100
        voice._record_until_silence = mock_record

        # Trigger
        try:
            await voice._process_active_interaction()
            print("  [OK] Scenario Pipeline Completed (Note: Automation execution depends on safety layer).")
        except Exception as e:
            if "Ollama" in str(e) or "connection attempts failed" in str(e).lower():
                print(f"  [!] Hardware Interaction Required: Ollama is not running. ({e})")
                print("  [!] Stopping test suite. Please run setup.ps1 and start Ollama.")
                break
            else:
                print(f"  [x] Pipeline Failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_integration_tests())
