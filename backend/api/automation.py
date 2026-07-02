from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text

from backend.api.deps import get_coordinator, get_memory_manager
from backend.automation.coordinator import ExecutionCoordinator
from backend.memory.manager import MemoryManager
from backend.planner.models import ExecutionPlan, TaskStep

router = APIRouter(prefix="/api/automation", tags=["automation"])


class AutomationPlanRequest(BaseModel):
    goal: str
    steps: list[dict[str, Any]]
    expected_output: str


class AutomationResponse(BaseModel):
    response: str


@router.post("", response_model=AutomationResponse)
async def trigger_automation(
    request: AutomationPlanRequest,
    coordinator: ExecutionCoordinator = Depends(get_coordinator),
) -> AutomationResponse:
    """Manually trigger an execution plan."""
    steps = [TaskStep(**s) for s in request.steps]
    plan = ExecutionPlan(
        goal=request.goal,
        steps=steps,
        expected_output=request.expected_output,
        plan_version="1.0",
        planner_version="1.0",
        required_tools=[],
        required_memory=[],
        dependencies=[],
        risks=[],
        confidence_score=1.0,
        confidence_reason="Manual",
        verification_strategy="",
        retry_strategy=""
    )
    result = await coordinator.execute_plan(plan)
    return AutomationResponse(response=result)


@router.get("/history", response_model=list[dict[str, Any]])
async def get_automation_history(
    memory_manager: MemoryManager = Depends(get_memory_manager),
) -> list[dict[str, Any]]:
    """Retrieve history of executed tasks."""
    try:
        result = await memory_manager.sql_repo._session.execute(
            text("SELECT * FROM tasks ORDER BY created_at DESC LIMIT 50")
        )
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    except Exception:
        return []
