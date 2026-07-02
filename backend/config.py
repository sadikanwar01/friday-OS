"""
FRIDAY OS — Configuration System.

Centralized configuration management using Pydantic v2 BaseSettings.
All settings are loaded from environment variables (prefixed with ``FRIDAY_``)
and an optional ``.env`` file at the project root.

Usage::

    from backend.config import get_settings

    settings = get_settings()
    print(settings.app_name)       # "FRIDAY OS"
    print(settings.is_development) # True
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, ClassVar

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VALID_ENVIRONMENTS: frozenset[str] = frozenset({"development", "staging", "production", "testing"})
_VALID_LOG_LEVELS: frozenset[str] = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
_VALID_SECURITY_MODES: frozenset[str] = frozenset({"safe", "confirm", "auto"})
_VALID_VOICE_MODES: frozenset[str] = frozenset({"wake_word", "push_to_talk"})


# ---------------------------------------------------------------------------
# Settings class
# ---------------------------------------------------------------------------


class Settings(BaseSettings):
    """Unified application settings for FRIDAY OS.

    Fields are grouped by logical section via a naming prefix
    (``app_``, ``api_``, ``db_``, etc.).  Each field maps to an
    environment variable of the form ``FRIDAY_<FIELD_NAME>``.

    Example:
        ``api_host`` ➜ ``FRIDAY_API_HOST``
    """

    model_config = SettingsConfigDict(
        env_prefix="FRIDAY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────────────────────────
    app_name: str = Field(
        default="FRIDAY OS",
        description="Display name of the application.",
    )
    app_version: str = Field(
        default="0.1.0",
        description="Semantic version string.",
    )
    app_env: str = Field(
        default="development",
        description="Runtime environment (development | staging | production).",
    )
    app_debug: bool = Field(
        default=True,
        description="Enable debug mode. Automatically disabled in production.",
    )
    app_log_level: str = Field(
        default="DEBUG",
        description="Minimum log level (DEBUG | INFO | WARNING | ERROR | CRITICAL).",
    )

    # ── API Server ───────────────────────────────────────────────────────
    api_host: str = Field(
        default="127.0.0.1",
        description="Host address for the API server.",
    )
    api_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port for the API server (1–65535).",
    )
    api_workers: int = Field(
        default=1,
        ge=1,
        description="Number of Uvicorn worker processes.",
    )
    api_cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins.",
    )

    # ── Database ─────────────────────────────────────────────────────────
    db_url: str = Field(
        default="sqlite+aiosqlite:///./data/friday.db",
        description="Async SQLAlchemy database URL.",
    )
    db_echo: bool = Field(
        default=False,
        description="Echo SQL statements to the log.",
    )

    # ── Security ─────────────────────────────────────────────────────────
    security_mode: str = Field(
        default="confirm",
        description="Execution safety mode (safe | confirm | auto).",
    )
    secret_key: str = Field(
        default="change-me-to-a-random-secret-key",
        description="Secret key for signing tokens and sessions.",
    )

    # ── LLM ─────────────────────────────────────────────────────────────
    default_provider: str = Field(
        default="gemini",
        description="Default LLM provider (ollama | gemini).",
    )
    llm_model: str = Field(
        default="", # Set dynamically in __init__ if empty
        description="Default LLM model to use system-wide.",
    )

    # ── LLM (Gemini) ────────────────────────────────────────────────────
    gemini_api_key: str | None = Field(
        default=None,
        description="API key for Google Gemini.",
    )
    gemini_model: str = Field(
        default="gemini-2.5-pro",
        description="Default Gemini model to use.",
    )

    # ── LLM (Ollama) ────────────────────────────────────────────────────
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL of the Ollama API.",
    )
    ollama_model: str = Field(
        default="llama3.1:8b",
        description="Default Ollama model to use.",
    )
    ollama_timeout: int = Field(
        default=120,
        ge=1,
        description="Request timeout in seconds for Ollama calls.",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.llm_model:
            self.llm_model = self.gemini_model if self.default_provider == "gemini" else self.ollama_model

    # ── Voice ────────────────────────────────────────────────────────────
    voice_wake_word: str = Field(
        default="friday",
        description="Trigger phrase for voice activation.",
    )
    voice_stt_model: str = Field(
        default="base",
        description="Whisper model size for speech-to-text.",
    )
    voice_tts_voice: str = Field(
        default="en-US-AriaNeural",
        description="TTS voice identifier.",
    )
    voice_language: str = Field(
        default="en",
        description="Primary language code for voice interactions.",
    )
    voice_mode: str = Field(
        default="wake_word",
        description="Operating mode (wake_word | push_to_talk).",
    )
    safety_mode: str = Field(
        default="confirm",
        description="Automation safety mode (safe | confirm | auto).",
    )

    # ── Paths ────────────────────────────────────────────────────────────
    data_dir: Path = Field(
        default=Path("./data"),
        description="Root data directory.",
    )
    logs_dir: Path = Field(
        default=Path("./data/logs"),
        description="Directory for log files.",
    )
    artifacts_dir: Path = Field(
        default=Path("./data/artifacts"),
        description="Directory for generated artifacts.",
    )
    chroma_dir: Path = Field(
        default=Path("./data/chroma"),
        description="Directory for ChromaDB vector store.",
    )

    # ── Class-level constants (not fields) ───────────────────────────────
    VALID_ENVIRONMENTS: ClassVar[frozenset[str]] = _VALID_ENVIRONMENTS
    VALID_LOG_LEVELS: ClassVar[frozenset[str]] = _VALID_LOG_LEVELS
    VALID_SECURITY_MODES: ClassVar[frozenset[str]] = _VALID_SECURITY_MODES
    VALID_VOICE_MODES: ClassVar[frozenset[str]] = _VALID_VOICE_MODES

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @model_validator(mode="before")
    @classmethod
    def load_unprefixed_env_vars(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Support explicitly required unprefixed env vars."""
        import os

        from dotenv import load_dotenv
        load_dotenv(override=True)

        mapping = {
            "GEMINI_API_KEY": "gemini_api_key",
            "DEFAULT_PROVIDER": "default_provider",
            "GEMINI_MODEL": "gemini_model",
        }

        for env_var, field_name in mapping.items():
            if env_var in os.environ and field_name not in data:
                data[field_name] = os.environ[env_var]

        return data

    @field_validator("app_env")
    @classmethod
    def _validate_environment(cls, value: str) -> str:
        """Ensure the environment is one of the allowed values."""
        normalised = value.strip().lower()
        if normalised not in _VALID_ENVIRONMENTS:
            msg = (
                f"Invalid environment '{value}'. "
                f"Must be one of: {', '.join(sorted(_VALID_ENVIRONMENTS))}"
            )
            raise ValueError(msg)
        return normalised

    @field_validator("app_log_level")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        """Ensure the log level is a standard Python logging level."""
        normalised = value.strip().upper()
        if normalised not in _VALID_LOG_LEVELS:
            msg = (
                f"Invalid log level '{value}'. "
                f"Must be one of: {', '.join(sorted(_VALID_LOG_LEVELS))}"
            )
            raise ValueError(msg)
        return normalised

    @field_validator("security_mode")
    @classmethod
    def _validate_security_mode(cls, value: str) -> str:
        """Ensure the security mode is one of the allowed values."""
        normalised = value.strip().lower()
        if normalised not in _VALID_SECURITY_MODES:
            msg = (
                f"Invalid security mode '{value}'. "
                f"Must be one of: {', '.join(sorted(_VALID_SECURITY_MODES))}"
            )
            raise ValueError(msg)
        return normalised

    @field_validator("voice_mode")
    @classmethod
    def _validate_voice_mode(cls, value: str) -> str:
        """Ensure the voice mode is one of the allowed values."""
        normalised = value.strip().lower()
        if normalised not in _VALID_VOICE_MODES:
            msg = (
                f"Invalid voice mode '{value}'. "
                f"Must be one of: {', '.join(sorted(_VALID_VOICE_MODES))}"
            )
            raise ValueError(msg)
        return normalised

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------

    @property
    def is_development(self) -> bool:
        """Return ``True`` when running in the development environment."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Return ``True`` when running in the production environment."""
        return self.app_env == "production"

    # ------------------------------------------------------------------
    # Directory & logging helpers
    # ------------------------------------------------------------------

    def ensure_directories(self) -> None:
        """Create all configured data directories if they do not exist.

        Directories created:
        - :pyattr:`data_dir`
        - :pyattr:`logs_dir`
        - :pyattr:`artifacts_dir`
        - :pyattr:`chroma_dir`
        """
        for directory in (self.data_dir, self.logs_dir, self.artifacts_dir, self.chroma_dir):
            directory.mkdir(parents=True, exist_ok=True)

    def setup_logging(self) -> None:
        """Configure the application-wide logging system.

        Attempts to delegate to the structured logger provided by
        ``backend.utils.logger``.  Falls back to the standard library
        ``logging.basicConfig`` when the utils package is not yet
        available (e.g. during early bootstrapping).
        """
        try:
            from backend.utils.logger import setup_logging as _setup_logging

            _setup_logging(
                log_level=self.app_log_level,
                log_dir=self.logs_dir,
                json_output=self.is_production,
            )
        except ImportError:
            # Utils module not yet available — fall back to stdlib logging.
            logging.basicConfig(
                level=getattr(logging, self.app_log_level, logging.DEBUG),
                format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Settings app={self.app_name!r} env={self.app_env!r} "
            f"api={self.api_host}:{self.api_port} debug={self.app_debug}>"
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the global :class:`Settings` singleton.

    On first call the instance is created, directories are ensured,
    and logging is configured.  Subsequent calls return the cached
    instance.

    Returns:
        The application :class:`Settings` instance.
    """
    global _settings  # noqa: PLW0603
    if _settings is None:
        _settings = Settings()
        _settings.ensure_directories()
        _settings.setup_logging()
    return _settings
