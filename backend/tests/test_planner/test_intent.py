"""Tests for Intent Detection."""

from unittest.mock import AsyncMock, patch

import pytest

from backend.planner.intent import IntentDetectionEngine
from backend.utils.exceptions import AgentError


@pytest.fixture
def mock_router():
    with patch("backend.planner.intent.provider_router") as router:
        provider = AsyncMock()
        router.get_provider_for_model.return_value = provider
        yield provider


@pytest.mark.asyncio
async def test_intent_detection_success(mock_router):
    """Test successful intent detection returning valid JSON."""
    mock_router.generate.return_value = (
        '{"primary_intent": "create_file", "complexity": "low", "requires_planning": false}'
    )

    engine = IntentDetectionEngine()
    intent = await engine.detect_intent("Create a file called test.txt")

    assert intent.primary_intent == "create_file"
    assert intent.complexity == "low"
    assert intent.requires_planning is False


@pytest.mark.asyncio
async def test_intent_detection_invalid_json(mock_router):
    """Test exception raised on invalid JSON."""
    mock_router.generate.return_value = '{"primary_intent": "create_file", "complexity": "low", "requires_planning": false'  # Missing brace

    engine = IntentDetectionEngine()
    with pytest.raises(AgentError) as exc:
        await engine.detect_intent("Create a file")

    assert exc.value.error_code == "INTENT_PARSE_ERROR"


@pytest.mark.asyncio
async def test_intent_detection_validation_error(mock_router):
    """Test exception raised on invalid schema."""
    mock_router.generate.return_value = (
        '{"primary_intent": "create_file", "complexity": "ultra"}'  # Invalid enum and missing field
    )

    engine = IntentDetectionEngine()
    with pytest.raises(AgentError) as exc:
        await engine.detect_intent("Create a file")

    assert exc.value.error_code == "INTENT_VALIDATION_ERROR"
