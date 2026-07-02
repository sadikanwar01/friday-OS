"""
FRIDAY OS - Planning Engine.

The orchestrator for the Hybrid Planner Architecture.
Executes the pipeline: Intent Detection -> Rule-based Analysis ->
Memory Context -> LLM Planning -> Plan Validation -> ExecutionPlan.
"""

from __future__ import annotations

import orjson
from pydantic import ValidationError

from backend.config import get_settings
from backend.llm.router import provider_router
from backend.memory.manager import MemoryManager
from backend.planner.analysis import PlannerContext, RuleBasedAnalyzer
from backend.planner.intent import IntentDetectionEngine
from backend.planner.models import ExecutionPlan
from backend.planner.validator import PlanValidator
from backend.utils.exceptions import AgentError
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# The schema definition helps local LLMs format the JSON properly.
EXECUTION_PLAN_SCHEMA = """{
  "plan_version": "1.0",
  "planner_version": "1.0.0",
  "goal": "string",
  "steps": [
    {
      "id": "step_1",
      "name": "string",
      "description": "string",
      "dependencies": ["list of previous step ids"],
      "assigned_agent": "string or null",
      "tool_name": "string or null (e.g. 'terminal')",
      "action": "string or null (e.g. 'run_command')",
      "kwargs": {"command": "string"}
    }
  ],
  "required_tools": ["string"],
  "required_memory": ["string"],
  "dependencies": ["string"],
  "risks": [
    {
      "description": "string",
      "severity": "low|medium|high|critical",
      "mitigation": "string"
    }
  ],
  "confidence_score": 0.95,
  "confidence_reason": "string",
  "verification_strategy": "string",
  "retry_strategy": "string",
  "expected_output": "string"
}"""


class PlanningEngine:
    """The hybrid task orchestration planner."""

    def __init__(self, memory_manager: MemoryManager) -> None:
        self.settings = get_settings()
        self.model = self.settings.llm_model

        # Pipeline components
        self.intent_engine = IntentDetectionEngine()
        self.analyzer = RuleBasedAnalyzer(memory_manager)
        self.validator = PlanValidator()

    async def generate_plan(self, user_id: str, user_input: str, intent=None) -> ExecutionPlan:
        """Run the full hybrid planning pipeline to produce an Execution Plan."""
        logger.info("planner_pipeline_started", user_input_length=len(user_input))

        # 1. Intent Detection
        if intent is None:
            intent = await self.intent_engine.detect_intent(user_input)

        # 2 & 3. Rule-based Analysis & Memory Context
        context = await self.analyzer.analyze(user_id, user_input, intent)

        # 4. LLM Planning
        system_prompt = self._build_planning_prompt(context)
        messages = [{"role": "user", "content": user_input}]

        provider = provider_router.get_provider_for_model(self.model)

        try:
            raw_response = await provider.generate(
                model=self.model,
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.2,  # Slightly creative but highly structured
                format="json",
            )

            parsed_data = orjson.loads(raw_response)
            plan = ExecutionPlan(**parsed_data)

        except (orjson.JSONDecodeError, ValidationError) as exc:
            logger.error("planner_generation_failed", error=str(exc))
            raise AgentError(
                message=f"Failed to generate a valid Execution Plan: {exc}",
                error_code="PLAN_GENERATION_ERROR",
                agent_name="PlanningEngine",
            ) from exc

        # 5. Plan Validation
        self.validator.validate(plan)

        logger.info("planner_pipeline_completed", steps=len(plan.steps))
        return plan

    def _build_planning_prompt(self, context: PlannerContext) -> str:
        """Construct the highly detailed system prompt for the planning LLM."""

        constraints_text = "\n".join(f"- {c}" for c in context.system_constraints)

        return f"""You are the Planning Engine for FRIDAY OS.
Your objective is to decompose the user's request into a strict Execution Plan.

## Detected Context
- Primary Intent: {context.intent.primary_intent}
- Complexity: {context.intent.complexity}
- Security Mode: {context.security_mode}

## Retrieved Memory Context
{context.memory_context}

## System Constraints (MUST OBEY)
{constraints_text}
- Do NOT execute the tasks yourself. You are only the planner.
- Create explicit step IDs (e.g., step_1, step_2) and map dependencies correctly.
- Evaluate risks realistically.

- You MUST format tool execution correctly. Available basic tool: `terminal` (action: `run_command`, kwargs: `{{"command": "<cmd>"}}`)

You MUST respond with valid JSON ONLY matching the following schema EXACTLY:
{EXECUTION_PLAN_SCHEMA}
"""
