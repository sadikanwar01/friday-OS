"""Tests for the hybrid Planning Engine."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.planner.analysis import PlannerContext
from backend.planner.engine import PlanningEngine
from backend.planner.models import Intent


@pytest.fixture
def mock_components():
    with (
        patch("backend.planner.engine.IntentDetectionEngine") as mock_intent_cls,
        patch("backend.planner.engine.RuleBasedAnalyzer") as mock_analyzer_cls,
        patch("backend.planner.engine.PlanValidator") as mock_validator_cls,
        patch("backend.planner.engine.provider_router") as mock_router,
    ):
        intent_engine = AsyncMock()
        mock_intent_cls.return_value = intent_engine

        analyzer = AsyncMock()
        mock_analyzer_cls.return_value = analyzer

        validator = MagicMock()
        mock_validator_cls.return_value = validator

        provider = AsyncMock()
        mock_router.get_provider_for_model.return_value = provider

        yield intent_engine, analyzer, validator, provider


@pytest.mark.asyncio
async def test_planning_engine_pipeline(mock_components):
    """Test the full engine pipeline succeeds with valid LLM output."""
    intent_engine, analyzer, validator, provider = mock_components

    # Setup mocks
    intent_engine.detect_intent.return_value = Intent(
        primary_intent="build", complexity="high", requires_planning=True
    )
    analyzer.analyze.return_value = PlannerContext(
        user_input="Build a server",
        intent=intent_engine.detect_intent.return_value,
        security_mode="safe",
        system_constraints=["No direct code execution"],
        memory_context="",
    )

    valid_plan_json = """{
        "plan_version": "1.0",
        "planner_version": "1.0.0",
        "goal": "Build server",
        "steps": [{"id": "s1", "name": "test", "description": "test", "dependencies": [], "assigned_agent": null}],
        "required_tools": [],
        "required_memory": [],
        "dependencies": [],
        "risks": [],
        "confidence_score": 0.9,
        "confidence_reason": "simple task",
        "verification_strategy": "run ping",
        "retry_strategy": "retry 3 times",
        "expected_output": "server running"
    }"""
    provider.generate.return_value = valid_plan_json

    engine = PlanningEngine(AsyncMock())
    plan = await engine.generate_plan("user_1", "Build a server")

    # Assert pipeline called sequentially
    intent_engine.detect_intent.assert_called_once_with("Build a server")
    analyzer.analyze.assert_called_once()
    provider.generate.assert_called_once()
    validator.validate.assert_called_once_with(plan)

    assert plan.goal == "Build server"
    assert len(plan.steps) == 1
    assert plan.confidence_score == 0.9
