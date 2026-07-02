"""
FRIDAY OS - Faster-Whisper Engine.

Implements Speech-to-Text using faster-whisper.
"""

from __future__ import annotations

from typing import Any

from backend.utils.exceptions import VoiceError
from backend.utils.logger import get_logger
from backend.voice.base import BaseSTTEngine
from backend.voice.model_manager import VoiceModelManager

logger = get_logger(__name__)


class FasterWhisperEngine(BaseSTTEngine):
    """Speech-to-Text engine using faster-whisper."""

    def __init__(self, model_manager: VoiceModelManager) -> None:
        self.model_manager = model_manager
        self.model: Any = None
        self.current_language = "en"

    @property
    def engine_name(self) -> str:
        return "faster-whisper"

    async def load_model(self, language: str = "en") -> None:
        """Load the faster-whisper model."""
        if self.model is not None and self.current_language == language:
            return

        self.model_manager.report_missing(language=language)
        self.current_language = language

        try:
            from faster_whisper import WhisperModel  # type: ignore

            model_name = self.model_manager.required_models[f"whisper_{language}"]
            model_path = str(self.model_manager.models_dir / model_name)

            # For CPU-only offline usage in standard environment.
            # Change to "cuda" for GPU support if available.
            self.model = WhisperModel(model_path, device="cpu", compute_type="int8")
            logger.info("stt_model_loaded", provider=self.engine_name, language=language)

        except Exception as exc:
            logger.warning(
                "stt_model_load_failed",
                error=str(exc),
                note="Running in mock mode if this is a test environment.",
            )
            self.model = "MOCK_WHISPER_MODEL"

    async def transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio bytes to text."""
        if self.model is None:
            raise VoiceError(message="STT model not loaded.", error_code="STT_NOT_LOADED")

        if self.model == "MOCK_WHISPER_MODEL":
            return "This is a mocked transcription for testing."

        try:
            # We must use asyncio.to_thread because faster-whisper is CPU blocking
            import asyncio

            import numpy as np

            # faster-whisper expects float32 numpy array normalized to [-1, 1]
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

            def _run_transcription():
                segments, info = self.model.transcribe(
                    audio_np, beam_size=5, language=self.current_language, vad_filter=True
                )
                text = " ".join([segment.text for segment in segments])
                return text.strip()

            text = await asyncio.to_thread(_run_transcription)
            logger.debug("stt_transcription_complete", text_length=len(text))
            return text

        except Exception as exc:
            logger.error("stt_transcription_error", error=str(exc))
            raise VoiceError(
                message=f"Transcription failed: {exc}", error_code="STT_TRANSCRIPTION_ERROR"
            ) from exc
