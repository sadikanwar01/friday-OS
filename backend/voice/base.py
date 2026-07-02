"""
FRIDAY OS - Voice Engine Abstract Interfaces.

Defines the contract that all voice integrations (STT, TTS, Wake Word)
must adhere to, allowing the Voice Engine to remain provider-agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class BaseWakeWordEngine(ABC):
    """Abstract base class for Wake Word detection engines."""

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Name of the wake word engine."""
        pass

    @abstractmethod
    async def load_model(self) -> None:
        """Load the wake word model into memory."""
        pass

    @abstractmethod
    def process_audio_chunk(self, audio_data: bytes) -> bool:
        """Process a chunk of audio and return True if wake word is detected."""
        pass


class BaseSTTEngine(ABC):
    """Abstract base class for Speech-to-Text engines."""

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Name of the STT engine."""
        pass

    @abstractmethod
    async def load_model(self, language: str = "en") -> None:
        """Load the STT model into memory."""
        pass

    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio bytes to text."""
        pass


class BaseTTSEngine(ABC):
    """Abstract base class for Text-to-Speech engines."""

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Name of the TTS engine."""
        pass

    @abstractmethod
    async def load_model(self, voice_profile: str = "en-US") -> None:
        """Load the TTS model into memory."""
        pass

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Synthesize text into audio bytes."""
        pass

    @abstractmethod
    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """Synthesize text and stream audio chunks."""
        # Yield empty bytes by default if not overridden
        yield b""


class BaseMicrophoneManager(ABC):
    """Abstract base class for Microphone hardware management."""

    @abstractmethod
    def start_listening(self) -> None:
        """Start the microphone audio stream."""
        pass

    @abstractmethod
    def stop_listening(self) -> None:
        """Stop the microphone audio stream."""
        pass

    @abstractmethod
    def read_chunk(self) -> bytes | None:
        """Read a chunk of audio data from the microphone buffer."""
        pass


class BaseSpeakerManager(ABC):
    """Abstract base class for Speaker hardware management."""

    @abstractmethod
    def play_audio(self, audio_data: bytes) -> None:
        """Play audio bytes through the speaker."""
        pass

    @abstractmethod
    def stop_playback(self) -> None:
        """Stop any ongoing audio playback."""
        pass
