import asyncio
from unittest.mock import AsyncMock, patch

from backend.planner.models import ExecutionPlan
from backend.voice.pipeline import VoiceSessionManager


async def main():
    print("Starting Voice Engine Verification (Phase 3)...")

    # We will patch the SessionManager to use offline mocks
    # so we can verify the pipeline logic without hardware or models
    with patch("backend.voice.pipeline.SoundDeviceMicrophone") as MockMic, \
         patch("backend.voice.pipeline.SoundDeviceSpeaker") as MockSpeaker, \
         patch("backend.voice.pipeline.OpenWakeWordEngine") as MockWake, \
         patch("backend.voice.pipeline.FasterWhisperEngine") as MockSTT, \
         patch("backend.voice.pipeline.PiperTTSEngine") as MockTTS, \
         patch("backend.voice.pipeline.provider_router"):

        # Mock Memory and Planner
        mock_memory = AsyncMock()
        mock_planner = AsyncMock()

        # We simulate a plan being generated
        dummy_plan = ExecutionPlan(
            plan_version="1.0",
            planner_version="1.0",
            goal="Test the Voice System",
            steps=[],
            confidence_score=0.99,
            confidence_reason="Simulated plan",
            verification_strategy="None",
            retry_strategy="None",
            expected_output="Success"
        )
        mock_planner.generate_plan.return_value = dummy_plan

        # Instantiate Manager
        manager = VoiceSessionManager(mock_memory, mock_planner)
        manager.operating_mode = "push_to_talk"

        # Apply Mocks internally
        manager.mic = MockMic()
        manager.speaker = MockSpeaker()
        manager.wakeword = MockWake()
        manager.stt = MockSTT()
        manager.tts = MockTTS()

        # Setup specific mock returns
        manager.wakeword.load_model = AsyncMock()
        manager.stt.load_model = AsyncMock()
        manager.tts.load_model = AsyncMock()
        manager._record_until_silence = AsyncMock(return_value=b"0" * 2000)
        manager.stt.transcribe = AsyncMock(return_value="Please test the voice system.")
        manager.tts.synthesize = AsyncMock(return_value=b"audio_bytes")

        print("\n[Test 1] Initializing Voice Engine...")
        await manager.initialize()
        print("  -> Initialization Successful! Models explicitly loaded via manager.")

        print("\n[Test 2] Triggering Push-to-Talk Pipeline...")
        await manager.trigger_push_to_talk()

        # Verification
        manager.stt.transcribe.assert_called_once()
        print(f"  -> STT Transcribed text: '{manager.stt.transcribe.return_value}'")

        manager.tts.synthesize.assert_called_once()
        tts_text_sent = manager.tts.synthesize.call_args[0][0]
        print(f"  -> TTS Synthesis requested for text: '{tts_text_sent}'")

        manager.speaker.play_audio.assert_called_once_with(b"audio_bytes")
        print("  -> Speaker successfully requested audio playback!")

        print("\nVerification Complete! The Offline Voice Engine orchestrates successfully.")


if __name__ == "__main__":
    asyncio.run(main())
