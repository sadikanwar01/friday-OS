"""
FRIDAY OS - Intent Detection Engine.

Analyzes raw user input to determine the core intent, complexity,
and whether a full execution plan is required.
"""

from __future__ import annotations

import orjson
from pydantic import ValidationError

from backend.config import get_settings
from backend.llm.router import provider_router
from backend.planner.models import Intent
from backend.utils.exceptions import AgentError
from backend.utils.logger import get_logger

logger = get_logger(__name__)

INTENT_SYSTEM_PROMPT = """You are the Intent Detection Engine for FRIDAY OS.
Analyze the user's request and determine:
1. The primary intent (e.g., 'create_file', 'query_data', 'small_talk').
2. The complexity (low, medium, high).
3. Whether it requires a full execution plan (true/false). Small talk or simple questions do not require planning.

You MUST respond with valid JSON ONLY matching this schema:
{
    "primary_intent": "string",
    "complexity": "low|medium|high",
    "requires_planning": true|false
}
"""


class IntentDetectionEngine:
    """Engine to detect user intent using the LLM Provider."""

    def __init__(self) -> None:
        self.settings = get_settings()
        # Default model could be overriden via settings
        self.model = getattr(self.settings, "llm_model", "llama3.1:8b")

    async def detect_intent(self, user_input: str) -> Intent:
        """Analyze user input and return a structured Intent object."""
        provider = provider_router.get_provider_for_model(self.model)

        messages = [{"role": "user", "content": user_input}]

        try:
            # We enforce JSON response via the prompt.
            # In Phase 2A, format="json" can be passed in kwargs for Ollama.
            raw_response = await provider.generate(
                model=self.model,
                messages=messages,
                system_prompt=INTENT_SYSTEM_PROMPT,
                temperature=0.1,
                format="json",
            )

            # Parse the JSON response
            parsed_data = orjson.loads(raw_response)
            intent = Intent(**parsed_data)

            logger.info(
                "intent_detected",
                primary_intent=intent.primary_intent,
                complexity=intent.complexity,
                requires_planning=intent.requires_planning,
            )
            return intent

        except orjson.JSONDecodeError as exc:
            logger.error("intent_json_parse_error", error=str(exc), raw=raw_response)
            raise AgentError(
                message="Failed to parse Intent JSON from LLM.",
                error_code="INTENT_PARSE_ERROR",
                agent_name="IntentDetectionEngine",
            ) from exc
        except ValidationError as exc:
            logger.error("intent_validation_error", error=str(exc))
            raise AgentError(
                message="Invalid Intent schema returned by LLM.",
                error_code="INTENT_VALIDATION_ERROR",
                agent_name="IntentDetectionEngine",
            ) from exc
        except Exception as exc:
            logger.error("intent_detection_failed", error=str(exc))
            raise AgentError(
                message=f"Intent detection failed: {exc}",
                error_code="INTENT_DETECTION_ERROR",
                agent_name="IntentDetectionEngine",
            ) from exc
