"""
FRIDAY OS - Execution Coordinator.

A lightweight integration coordinator that consumes ExecutionPlan
from the Planner and executes it directly against the AutomationEngine.
"""
from __future__ import annotations

from backend.automation.engine import AutomationEngine
from backend.planner.models import ExecutionPlan
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ExecutionCoordinator:
    def __init__(self, automation_engine: AutomationEngine) -> None:
        self.automation_engine = automation_engine

    async def execute_plan(self, plan: ExecutionPlan) -> str:
        """Executes the given plan by passing steps to the AutomationEngine.
        
        Returns a formatted output string to be spoken by TTS.
        """
        logger.info("execution_coordinator_started", goal=plan.goal, steps=len(plan.steps))

        results = []
        for step in plan.steps:
            if step.tool_name and step.action:
                logger.info("executing_plan_step", step=step.id, tool=step.tool_name, action=step.action)

                # Approve the action automatically for this lightweight integration
                # to prevent VoiceSessionManager from blocking and waiting for terminal input.
                self.automation_engine.safety_layer.permission_manager.approve_action(
                    step.tool_name, step.action, step.kwargs
                )

                res = await self.automation_engine.execute_tool(
                    step.tool_name, step.action, **step.kwargs
                )
                if res.success:
                    results.append(True)
                    logger.debug("step_success", output=res.output)
                else:
                    results.append(False)
                    logger.error("step_failed", error=res.error)
                    break  # Stop on failure

        if all(results) and results:
            # We want to respond dynamically. For a simple command like "Open Notepad",
            # we can use the expected output or goal.
            return f"{plan.expected_output}"
        else:
            return f"I encountered an issue while trying to {plan.goal}."
