"""Tests for the Voice Pipeline Session Manager."""

from unittest.mock import AsyncMock, patch

import pytest

from backend.planner.models import ExecutionPlan
from backend.voice.pipeline import VoiceSessionManager


@pytest.fixture
def mock_session_manager():
    with (
        patch("backend.voice.pipeline.VoiceModelManager"),
        patch("backend.voice.pipeline.SoundDeviceMicrophone"),
        patch("backend.voice.pipeline.SoundDeviceSpeaker"),
        patch("backend.voice.pipeline.OpenWakeWordEngine") as mock_wake_cls,
        patch("backend.voice.pipeline.FasterWhisperEngine") as mock_stt_cls,
        patch("backend.voice.pipeline.PiperTTSEngine") as mock_tts_cls,
    ):
        memory_manager = AsyncMock()
        planning_engine = AsyncMock()

        manager = VoiceSessionManager(memory_manager, planning_engine)
        manager.wakeword = mock_wake_cls()
        manager.stt = mock_stt_cls()
        manager.tts = mock_tts_cls()

        manager.wakeword.load_model = AsyncMock()
        manager.stt.load_model = AsyncMock()
        manager.stt.transcribe = AsyncMock()
        manager.tts.load_model = AsyncMock()
        manager.tts.synthesize = AsyncMock()

        yield manager


@pytest.mark.asyncio
async def test_session_manager_initialization(mock_session_manager):
    """Test model loading during initialization."""
    mock_session_manager.operating_mode = "wake_word"
    mock_session_manager.language = "en"

    await mock_session_manager.initialize()

    mock_session_manager.wakeword.load_model.assert_called_once()
    mock_session_manager.stt.load_model.assert_called_once_with("en")
    mock_session_manager.tts.load_model.assert_called_once_with("en")


@pytest.mark.asyncio
async def test_process_active_interaction_plan_generated(mock_session_manager):
    """Test a full interaction where a plan is generated."""
    # Setup mocks
    mock_session_manager._record_until_silence = AsyncMock(return_value=b"0" * 2000)
    mock_session_manager.stt.transcribe = AsyncMock(return_value="Build a website")

    dummy_plan = ExecutionPlan(
        plan_version="1.0",
        planner_version="1.0",
        goal="Build website",
        steps=[],
        confidence_score=0.9,
        confidence_reason="reason",
        verification_strategy="check",
        retry_strategy="none",
        expected_output="website",
    )
    mock_session_manager.planning_engine.generate_plan.return_value = dummy_plan
    mock_session_manager.tts.synthesize = AsyncMock(return_value=b"audio")

    # Run
    await mock_session_manager._process_active_interaction()

    # Asserts
    mock_session_manager.stt.transcribe.assert_called_once()
    mock_session_manager.planning_engine.generate_plan.assert_called_once_with(
        user_id="default", user_input="Build a website"
    )
    mock_session_manager.tts.synthesize.assert_called_once()

    # Check if TTS was told about the plan
    tts_args = mock_session_manager.tts.synthesize.call_args[0][0]
    assert "I've created a plan to Build website" in tts_args
