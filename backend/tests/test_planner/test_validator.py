"""Tests for PlanValidator."""

import pytest

from backend.planner.models import ExecutionPlan, TaskStep
from backend.planner.validator import PlanValidator
from backend.utils.exceptions import AgentError


def create_dummy_plan(**kwargs):
    default_args = {
        "goal": "test",
        "steps": [TaskStep(id="s1", name="step1", description="desc", dependencies=[])],
        "confidence_score": 0.9,
        "confidence_reason": "reason",
        "verification_strategy": "verify",
        "retry_strategy": "retry",
        "expected_output": "output",
    }
    default_args.update(kwargs)
    return ExecutionPlan(**default_args)


def test_validator_success():
    """Test valid plan passes."""
    plan = create_dummy_plan()
    validator = PlanValidator()
    assert validator.validate(plan) is True


def test_validator_no_steps():
    """Test plan with no steps fails."""
    plan = create_dummy_plan(steps=[])
    validator = PlanValidator()
    with pytest.raises(AgentError) as exc:
        validator.validate(plan)
    assert exc.value.error_code == "PLAN_VALIDATION_NO_STEPS"


def test_validator_missing_dependency():
    """Test plan with unresolved dependency fails."""
    plan = create_dummy_plan(
        steps=[TaskStep(id="s1", name="step1", description="desc", dependencies=["s2"])]
    )
    validator = PlanValidator()
    with pytest.raises(AgentError) as exc:
        validator.validate(plan)
    assert exc.value.error_code == "PLAN_VALIDATION_MISSING_DEPENDENCY"


def test_validator_low_confidence():
    """Test plan with low confidence fails."""
    plan = create_dummy_plan(confidence_score=0.1)
    validator = PlanValidator()
    with pytest.raises(AgentError) as exc:
        validator.validate(plan)
    assert exc.value.error_code == "PLAN_VALIDATION_LOW_CONFIDENCE"
