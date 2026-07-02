"""
FRIDAY OS - Voice Session Manager & Pipeline.

Orchestrates the full offline voice pipeline:
Microphone -> Wake Word -> STT -> Brain (LLM/Memory/Planner) -> TTS -> Speaker
Supports both Push-to-Talk and Wake Word operating modes.
"""

from __future__ import annotations

import asyncio
from typing import Literal

from backend.automation.coordinator import ExecutionCoordinator
from backend.config import get_settings
from backend.llm.router import provider_router
from backend.memory.manager import MemoryManager
from backend.planner.engine import PlanningEngine
from backend.utils.exceptions import VoiceError
from backend.utils.logger import get_logger
from backend.voice.audio import SoundDeviceMicrophone, SoundDeviceSpeaker
from backend.voice.model_manager import VoiceModelManager
from backend.voice.providers.faster_whisper import FasterWhisperEngine
from backend.voice.providers.openwakeword import OpenWakeWordEngine
from backend.voice.providers.piper_tts import PiperTTSEngine

logger = get_logger(__name__)


class VoiceSessionManager:
    """Manages the lifecycle of a voice interaction."""

    def __init__(
        self,
        memory_manager: MemoryManager,
        planning_engine: PlanningEngine,
        execution_coordinator: ExecutionCoordinator | None = None
    ) -> None:
        self.settings = get_settings()
        self.language = getattr(self.settings, "voice_language", "en")
        self.operating_mode: Literal["wake_word", "push_to_talk"] = getattr(
            self.settings, "voice_mode", "wake_word"
        )
        self.llm_model = getattr(self.settings, "llm_model", "llama3.1:8b")

        self.memory_manager = memory_manager
        self.planning_engine = planning_engine
        self.execution_coordinator = execution_coordinator

        self.model_manager = VoiceModelManager()
        self.mic = SoundDeviceMicrophone()
        self.speaker = SoundDeviceSpeaker()

        self.wakeword = OpenWakeWordEngine(self.model_manager)
        self.stt = FasterWhisperEngine(self.model_manager)
        self.tts = PiperTTSEngine(self.model_manager)

        self._is_running = False

    async def initialize(self) -> None:
        """Initialize models and ensure they are downloaded/available."""
        logger.info("initializing_voice_engine", mode=self.operating_mode, language=self.language)

        # Load required models (Raises ConfigurationError if missing)
        if self.operating_mode == "wake_word":
            await self.wakeword.load_model()

        await self.stt.load_model(self.language)
        await self.tts.load_model(self.language)

        logger.info("voice_engine_initialized")

    async def start(self) -> None:
        """Start the background voice processing pipeline."""
        if self._is_running:
            return

        await self.initialize()
        self._is_running = True

        if self.operating_mode == "wake_word":
            asyncio.create_task(self._wake_word_loop())
        else:
            logger.info("voice_push_to_talk_ready")

    def stop(self) -> None:
        """Stop the voice pipeline."""
        self._is_running = False
        self.mic.stop_listening()
        self.speaker.stop_playback()
        logger.info("voice_engine_stopped")

    async def _wake_word_loop(self) -> None:
        """Continuously listen for the wake word."""
        self.mic.start_listening()
        logger.info("listening_for_wake_word")

        try:
            while self._is_running:
                chunk = self.mic.read_chunk()
                if chunk and self.wakeword.process_audio_chunk(chunk):
                    logger.info("wake_word_triggered")
                    await self._process_active_interaction()
                await asyncio.sleep(0.01)
        except Exception as exc:
            logger.error("wake_word_loop_crashed", error=str(exc))
        finally:
            self.mic.stop_listening()

    async def trigger_push_to_talk(self) -> None:
        """Manually trigger an active interaction (Push-to-Talk)."""
        if self.operating_mode != "push_to_talk":
            logger.warning("push_to_talk_invoked_in_wakeword_mode")

        logger.info("push_to_talk_triggered")
        await self._process_active_interaction()

    async def _record_until_silence(self) -> bytes:
        """Record audio from the microphone until silence is detected.

        Note: For Phase 3 offline architecture validation, we implement a simple
        fixed duration recording or mock logic if running headless. A robust VAD
        (Voice Activity Detection) would normally be used here.
        """
        # In a real implementation with PyAudio/sounddevice, we'd accumulate chunks
        # and measure RMS energy. For this implementation, we accumulate 3 seconds.
        self.mic.start_listening()
        audio_buffer = bytearray()

        # Record for 3 seconds max (simplified VAD)
        for _ in range(30):
            if not self._is_running:
                break
            chunk = self.mic.read_chunk()
            if chunk:
                audio_buffer.extend(chunk)
            await asyncio.sleep(0.1)

        self.mic.stop_listening()
        return bytes(audio_buffer)

    async def _process_active_interaction(self) -> None:
        """Handle STT -> Brain -> TTS pipeline."""
        try:
            # 1. Record Audio
            logger.info("recording_user_audio")
            audio_data = await self._record_until_silence()
            if len(audio_data) < 1000:
                logger.debug("audio_too_short_ignoring")
                return

            # 2. STT
            user_text = await self.stt.transcribe(audio_data)
            if not user_text:
                return
            logger.info("user_speech_transcribed", text=user_text)

            # 3. Brain Processing (Planner -> LLM)
            # Route to planner to see if it's a complex task
            try:
                plan = await self.planning_engine.generate_plan(
                    user_id="default", user_input=user_text
                )

                if plan.goal:
                    if self.execution_coordinator:
                        response_text = await self.execution_coordinator.execute_plan(plan)
                    else:
                        response_text = f"I've created a plan to {plan.goal}. However, execution is not yet implemented."
                else:
                    response_text = "I processed your request but no plan was generated."

            except Exception:
                # If planning fails or is simple small talk, fallback to standard LLM
                provider = provider_router.get_provider_for_model(self.llm_model)
                response_text = await provider.generate(
                    model=self.llm_model,
                    messages=[{"role": "user", "content": user_text}],
                    system_prompt="You are FRIDAY. You were designed and developed by Professor Sadiq. Your reasoning engine is powered by Google's Gemini models. Never identify as Gemini or Google AI. Be concise.",
                )

            logger.info("brain_generated_response", text=response_text)

            # 4. TTS and Playback
            logger.info("synthesizing_speech")
            audio_response = await self.tts.synthesize(response_text)
            self.speaker.play_audio(audio_response)

        except VoiceError as ve:
            logger.error("voice_interaction_failed", error=str(ve))
        except Exception as exc:
            logger.error("unexpected_voice_error", error=str(exc))

        # Ensure mic is ready for next iteration if in wake word mode
        if self._is_running and self.operating_mode == "wake_word":
            self.mic.start_listening()
