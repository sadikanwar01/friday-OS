"""
FRIDAY OS - Audio Hardware Management.

Implements Microphone and Speaker managers using `sounddevice` and `numpy`.
Provides streaming audio capture and playback.
"""

from __future__ import annotations

import contextlib
import queue
from typing import Any

import numpy as np
import sounddevice as sd  # type: ignore

from backend.utils.exceptions import VoiceError
from backend.utils.logger import get_logger
from backend.voice.base import BaseMicrophoneManager, BaseSpeakerManager

logger = get_logger(__name__)


class SoundDeviceMicrophone(BaseMicrophoneManager):
    """Manages audio input streaming using sounddevice."""

    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1280) -> None:
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue: queue.Queue[bytes] = queue.Queue()
        self.stream: sd.InputStream | None = None
        self.is_listening = False

    def _audio_callback(
        self, indata: np.ndarray, frames: int, time_info: Any, status: sd.CallbackFlags
    ) -> None:
        """Callback invoked by sounddevice for each audio chunk."""
        if status:
            logger.warning("microphone_status_warning", status=str(status))

        if self.is_listening:
            # Convert float32 numpy array to int16 bytes which is standard for wakeword/STT
            audio_data = (indata[:, 0] * 32767).astype(np.int16).tobytes()
            with contextlib.suppress(queue.Full):
                self.audio_queue.put_nowait(audio_data)

    def start_listening(self) -> None:
        """Start the microphone audio stream."""
        if self.stream is not None:
            return

        logger.info("microphone_starting", sample_rate=self.sample_rate)

        try:
            # Clear the queue
            while not self.audio_queue.empty():
                self.audio_queue.get_nowait()

            self.is_listening = True
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                blocksize=self.chunk_size,
                callback=self._audio_callback,
            )
            self.stream.start()
        except Exception as exc:
            self.is_listening = False
            self.stream = None
            logger.error("microphone_start_failed", error=str(exc))
            raise VoiceError(
                message=f"Failed to start microphone: {exc}", error_code="MIC_START_ERROR"
            ) from exc

    def stop_listening(self) -> None:
        """Stop the microphone audio stream."""
        self.is_listening = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        logger.info("microphone_stopped")

    def read_chunk(self) -> bytes | None:
        """Read a chunk of audio data from the microphone buffer."""
        try:
            return self.audio_queue.get(timeout=0.1)
        except queue.Empty:
            return None


class SoundDeviceSpeaker(BaseSpeakerManager):
    """Manages audio output using sounddevice."""

    def __init__(self, sample_rate: int = 22050) -> None:
        # Piper TTS usually outputs 22050Hz by default
        self.sample_rate = sample_rate

    def play_audio(self, audio_data: bytes) -> None:
        """Play audio bytes through the speaker.

        Expects int16 PCM bytes. Blocks until playback is finished.
        """
        try:
            # Convert int16 bytes to numpy array
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            sd.play(audio_np, samplerate=self.sample_rate, blocking=True)
        except Exception as exc:
            logger.error("speaker_playback_failed", error=str(exc))
            raise VoiceError(
                message=f"Failed to play audio: {exc}", error_code="SPEAKER_PLAY_ERROR"
            ) from exc

    def stop_playback(self) -> None:
        """Stop any ongoing audio playback."""
        sd.stop()
        logger.info("speaker_stopped")
