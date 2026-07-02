import asyncio

from backend.automation.coordinator import ExecutionCoordinator
from backend.automation.engine import AutomationEngine
from backend.automation.registry import ToolRegistry
from backend.automation.safety import PermissionManager, SafetyLayer
from backend.automation.tools.terminal import TerminalTool
from backend.config import get_settings
from backend.database import async_session_factory, init_database
from backend.memory.manager import MemoryManager
from backend.planner.engine import PlanningEngine
from backend.voice.pipeline import VoiceSessionManager


async def test_main():
    print("Testing End-to-End Pipeline...")
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

    engine = AutomationEngine(registry, safety)
    coordinator = ExecutionCoordinator(engine)

    # We will mock STT and TTS to run in CI
    voice = VoiceSessionManager(memory, planner, coordinator)

    # Mocking STT to return "Open Notepad"
    async def mock_transcribe(audio):
        print("\n[User]: Open Notepad.")
        return "Open Notepad."

    # Mocking TTS so we can see the output
    async def mock_synthesize(text):
        print(f"[FRIDAY]: {text}")
        return b""

    voice.stt.transcribe = mock_transcribe
    voice.tts.synthesize = mock_synthesize

    # Mock record to avoid blocking on mic
    async def mock_record():
        return b"fake_audio_data" * 1000
    voice._record_until_silence = mock_record

    # Mock play audio
    def mock_play(audio):
        pass
    voice.speaker.play_audio = mock_play
    async def mock_initialize():
        pass
    voice.initialize = mock_initialize

    await voice.initialize()

    print("\nTriggering pipeline...")
    await voice._process_active_interaction()

    print("\nVerification Complete!")

if __name__ == "__main__":
    asyncio.run(test_main())
