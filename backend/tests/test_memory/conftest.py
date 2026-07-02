import sys
from unittest.mock import MagicMock

# Mock chromadb globally if it fails to import due to Windows file lock issues during install
try:
    import chromadb  # type: ignore # noqa: F401
except ImportError:
    mock_chromadb = MagicMock()
    mock_chromadb.PersistentClient = MagicMock()

    mock_settings = MagicMock()
    mock_chromadb.config = MagicMock()
    mock_chromadb.config.Settings = mock_settings

    sys.modules["chromadb"] = mock_chromadb
    sys.modules["chromadb.config"] = mock_chromadb.config
