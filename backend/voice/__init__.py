"""
FRIDAY OS - Voice Engine Module (Phase 3).

Provides fully offline Wake Word, Speech-to-Text, Text-to-Speech,
and audio hardware management components.
"""

from __future__ import annotations

from backend.voice.audio import SoundDeviceMicrophone, SoundDeviceSpeaker
from backend.voice.base import (
    BaseMicrophoneManager,
    BaseSpeakerManager,
    BaseSTTEngine,
    BaseTTSEngine,
    BaseWakeWordEngine,
)
from backend.voice.model_manager import VoiceModelManager
from backend.voice.pipeline import VoiceSessionManager
from backend.voice.providers.faster_whisper import FasterWhisperEngine
from backend.voice.providers.openwakeword import OpenWakeWordEngine
from backend.voice.providers.piper_tts import PiperTTSEngine

__all__ = [
    "BaseMicrophoneManager",
    "BaseSTTEngine",
    "BaseSpeakerManager",
    "BaseTTSEngine",
    "BaseWakeWordEngine",
    "FasterWhisperEngine",
    "OpenWakeWordEngine",
    "PiperTTSEngine",
    "SoundDeviceMicrophone",
    "SoundDeviceSpeaker",
    "VoiceModelManager",
    "VoiceSessionManager",
]
