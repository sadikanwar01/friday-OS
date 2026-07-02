"""Tests for Audio Management."""

from unittest.mock import patch

import numpy as np

from backend.voice.audio import SoundDeviceMicrophone, SoundDeviceSpeaker


def test_microphone_start_stop():
    """Test starting and stopping microphone."""
    with patch("backend.voice.audio.sd.InputStream") as mock_stream:
        mic = SoundDeviceMicrophone()

        mic.start_listening()
        assert mic.is_listening is True
        mock_stream.assert_called_once()

        mic.stop_listening()
        assert mic.is_listening is False


def test_microphone_callback():
    """Test microphone callback queues data."""
    mic = SoundDeviceMicrophone()
    mic.is_listening = True

    # Mock sounddevice audio input (frames x channels)
    dummy_data = np.zeros((1024, 1), dtype=np.float32)
    mic._audio_callback(dummy_data, 1024, None, None)

    # Check queue
    queued_bytes = mic.read_chunk()
    assert queued_bytes is not None
    assert len(queued_bytes) > 0


def test_speaker_playback():
    """Test speaker plays data."""
    with patch("backend.voice.audio.sd.play") as mock_play:
        speaker = SoundDeviceSpeaker()
        dummy_audio = b"\x00" * 1024

        speaker.play_audio(dummy_audio)
        mock_play.assert_called_once()
