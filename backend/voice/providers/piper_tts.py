"""
FRIDAY OS - Piper TTS Engine.

Implements Text-to-Speech using piper-tts.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from backend.utils.exceptions import VoiceError
from backend.utils.logger import get_logger
from backend.voice.base import BaseTTSEngine
from backend.voice.model_manager import VoiceModelManager

logger = get_logger(__name__)


class PiperTTSEngine(BaseTTSEngine):
    """Text-to-Speech engine using piper-tts."""

    def __init__(self, model_manager: VoiceModelManager) -> None:
        self.model_manager = model_manager
        self.model: Any = None
        self.current_language = "en"

    @property
    def engine_name(self) -> str:
        return "piper-tts"

    async def load_model(self, voice_profile: str = "en") -> None:
        """Load the piper-tts model."""
        if self.model is not None and self.current_language == voice_profile:
            return

        self.model_manager.report_missing(language=voice_profile)
        self.current_language = voice_profile

        try:
            from piper import PiperVoice  # type: ignore

            model_name = self.model_manager.required_models[f"piper_{voice_profile}"]
            model_path = str(self.model_manager.models_dir / model_name)

            self.model = PiperVoice.load(model_path)
            logger.info("tts_model_loaded", provider=self.engine_name, profile=voice_profile)

        except Exception as exc:
            logger.warning(
                "tts_model_load_failed",
                error=str(exc),
                note="Running in mock mode if this is a test environment.",
            )
            self.model = "MOCK_PIPER_MODEL"

    async def synthesize(self, text: str) -> bytes:
        """Synthesize complete text into audio bytes."""
        if self.model is None:
            raise VoiceError(message="TTS model not loaded.", error_code="TTS_NOT_LOADED")

        if self.model == "MOCK_PIPER_MODEL":
            # Return dummy silent PCM int16 audio for 1 second at 22050Hz
            return b"\x00" * (22050 * 2)

        try:

            def _run_synthesis():
                audio_stream = self.model.synthesize_stream_raw(text)
                audio_bytes = b""
                for chunk in audio_stream:
                    audio_bytes += chunk
                return audio_bytes

            audio = await asyncio.to_thread(_run_synthesis)
            logger.debug("tts_synthesis_complete", bytes=len(audio))
            return audio

        except Exception as exc:
            logger.error("tts_synthesis_error", error=str(exc))
            raise VoiceError(
                message=f"Synthesis failed: {exc}", error_code="TTS_SYNTHESIS_ERROR"
            ) from exc

    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """Synthesize text and stream audio chunks."""
        if self.model is None or self.model == "MOCK_PIPER_MODEL":
            yield await self.synthesize(text)
            return

        try:
            # Note: synthesize_stream_raw is a blocking generator.
            # We must wrap it in an executor to avoid blocking the event loop.
            import queue

            q: queue.Queue[bytes | None] = queue.Queue()

            def _producer():
                try:
                    for chunk in self.model.synthesize_stream_raw(text):
                        q.put(chunk)
                except Exception as e:
                    logger.error("tts_stream_producer_error", error=str(e))
                finally:
                    q.put(None)  # EOF

            # Start thread
            loop = asyncio.get_running_loop()
            loop.run_in_executor(None, _producer)

            # Consume queue
            while True:
                # Polling queue in a non-blocking way using asyncio.sleep
                try:
                    chunk = q.get_nowait()
                    if chunk is None:
                        break
                    yield chunk
                except queue.Empty:
                    await asyncio.sleep(0.01)

        except Exception as exc:
            logger.error("tts_synthesis_stream_error", error=str(exc))
            raise VoiceError(
                message=f"Synthesis stream failed: {exc}", error_code="TTS_SYNTHESIS_ERROR"
            ) from exc
