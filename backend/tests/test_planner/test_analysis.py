"""Tests for Rule-based Analysis."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.planner.analysis import RuleBasedAnalyzer
from backend.planner.models import Intent


@pytest.fixture
def mock_memory_manager():
    manager = AsyncMock()
    # Mock search to return empty by default
    manager.search.return_value = []
    return manager


@pytest.mark.asyncio
async def test_analyzer_safe_mode(mock_memory_manager):
    """Test analyzer injects correct constraints based on settings and intent."""
    analyzer = RuleBasedAnalyzer(mock_memory_manager)
    analyzer.settings.security_mode = "safe"

    intent = Intent(primary_intent="test", complexity="high", requires_planning=True)

    context = await analyzer.analyze("user_1", "Test input", intent)

    assert context.security_mode == "safe"
    # Should include base constraint + safe mode constraints + high complexity constraints
    assert len(context.system_constraints) >= 5
    assert any("forbidden" in c for c in context.system_constraints)
    assert any("highly detailed steps" in c for c in context.system_constraints)


@pytest.mark.asyncio
async def test_analyzer_memory_retrieval(mock_memory_manager):
    """Test analyzer formats memory correctly."""
    mock_mem = MagicMock()
    mock_mem.key = "preference"
    mock_mem.value = "likes dark mode"
    mock_memory_manager.search.return_value = [mock_mem]

    analyzer = RuleBasedAnalyzer(mock_memory_manager)
    intent = Intent(primary_intent="test", complexity="low", requires_planning=False)

    context = await analyzer.analyze("user_1", "Test input", intent)

    assert "preference: likes dark mode" in context.memory_context
