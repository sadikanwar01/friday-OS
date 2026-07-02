"""
FRIDAY OS - Rule-Based Analysis Engine.

Performs static analysis on the user input and detected intent before
passing it to the LLM. Gathers relevant context from the Memory System
and applies FRIDAY OS constraints.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.config import get_settings
from backend.memory.manager import MemoryManager
from backend.planner.models import Intent
from backend.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PlannerContext:
    """The complete context gathered for the LLM Planning phase."""

    user_input: str
    intent: Intent
    security_mode: str
    system_constraints: list[str]
    memory_context: str


class RuleBasedAnalyzer:
    """Applies rules and gathers memory context for the planner."""

    def __init__(self, memory_manager: MemoryManager) -> None:
        self.settings = get_settings()
        self.memory_manager = memory_manager

    async def analyze(self, user_id: str, user_input: str, intent: Intent) -> PlannerContext:
        """Run rule-based analysis and context aggregation."""
        logger.debug("starting_rule_based_analysis", intent=intent.primary_intent)

        # 1. Rule-based Constraints
        # Based on the user's security mode and intent, we inject hard rules
        # that the LLM Planner MUST obey.
        # Note: In a real system, security_mode might be fetched from the User model.
        # For Phase 2C, we use the global setting as default.
        security_mode = getattr(self.settings, "security_mode", "confirm")

        constraints = [
            "Do NOT execute any code directly.",
            "Output ONLY the requested JSON schema.",
        ]

        if security_mode == "safe":
            constraints.append("Plan must include verification steps for ANY file modification.")
            constraints.append("High risk commands are forbidden.")
        elif security_mode == "confirm":
            constraints.append(
                "Plan must explicitly require user confirmation for destructive actions."
            )

        if intent.complexity == "high":
            constraints.append("Break the task down into smaller, highly detailed steps.")
            constraints.append("Include explicit retry strategies for network operations.")

        # 2. Memory Context Gathering
        # Fetch relevant semantic memories based on the user's input.
        try:
            memories = await self.memory_manager.search(user_id=user_id, query=user_input, limit=5)
            if memories:
                memory_texts = [f"- {m.key}: {m.value}" for m in memories]
                memory_context = "\n".join(memory_texts)
            else:
                memory_context = "No relevant past memories found."
        except Exception as exc:
            logger.warning("memory_context_gather_failed", error=str(exc))
            memory_context = "Memory system unavailable."

        logger.info(
            "rule_based_analysis_complete",
            constraints_count=len(constraints),
            memory_found=bool(memories),
        )

        return PlannerContext(
            user_input=user_input,
            intent=intent,
            security_mode=security_mode,
            system_constraints=constraints,
            memory_context=memory_context,
        )
