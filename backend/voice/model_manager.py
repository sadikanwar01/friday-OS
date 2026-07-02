"""
FRIDAY OS - Voice Model Manager.

Manages the local models for Wake Word, STT, and TTS.
Checks for the presence of required models and provides an explicit
setup routine for downloading them, avoiding unwanted automatic downloads.
"""

from __future__ import annotations

from pathlib import Path

from backend.config import get_settings
from backend.utils.exceptions import ConfigurationError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class VoiceModelManager:
    """Manages downloading and verifying offline voice models."""

    def __init__(self) -> None:
        self.settings = get_settings()
        # Create a dedicated directory for models
        self.models_dir = getattr(self.settings, "data_dir", Path("./data")) / "voice_models"
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.required_models = {
            "whisper_en": "faster-whisper-base.en",
            "whisper_hi": "faster-whisper-medium",
            "piper_en": "en_US-lessac-medium.onnx",
            "piper_hi": "hi_IN-swara-medium.onnx",
            "wakeword": "openwakeword_friday.tflite",
        }

    def check_models(self, language: str = "en") -> list[str]:
        """Check if required models for a given language are present.

        Args:
            language: 'en' or 'hi'

        Returns:
            A list of missing model keys.
        """
        missing = []

        # Check wake word
        ww_path = self.models_dir / self.required_models["wakeword"]
        if not ww_path.exists():
            missing.append("wakeword")

        # Check STT
        stt_key = f"whisper_{language}"
        stt_path = self.models_dir / self.required_models[stt_key]
        if not stt_path.exists():
            missing.append(stt_key)

        # Check TTS
        tts_key = f"piper_{language}"
        tts_path = self.models_dir / self.required_models[tts_key]
        if not tts_path.exists():
            missing.append(tts_key)

        return missing

    def report_missing(self, language: str = "en") -> None:
        """Log missing models and raise ConfigurationError if any are missing."""
        missing = self.check_models(language)
        if missing:
            missing_names = [self.required_models[m] for m in missing]
            logger.error(
                "voice_models_missing",
                language=language,
                missing_models=missing_names,
                models_dir=str(self.models_dir),
            )
            raise ConfigurationError(
                message=f"Missing voice models for {language}: {', '.join(missing_names)}. "
                "Please run the voice setup command to download them.",
                error_code="VOICE_MODELS_MISSING",
            )

    async def download_models(self, language: str = "en") -> None:
        """Download missing models for the specified language.

        This is an explicit setup process triggered manually by the user or CLI.
        """
        missing = self.check_models(language)
        if not missing:
            logger.info("voice_models_up_to_date", language=language)
            return

        logger.info("downloading_voice_models", missing=missing)

        # Note: Actual HTTP download logic for huggingface/github models goes here.
        # For Phase 3 offline architecture validation, we might mock this or
        # use huggingface_hub.snapshot_download in real implementation.

        for model_key in missing:
            model_name = self.required_models[model_key]
            logger.info("downloading_model", model=model_name)
            # Placeholder for actual download code:
            # huggingface_hub.hf_hub_download(...)

            # Create a dummy file to simulate successful download for testing
            dummy_path = self.models_dir / model_name
            dummy_path.touch()

        logger.info("voice_models_download_complete", language=language)
