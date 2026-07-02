"""
FRIDAY OS - Conversation Engine.

The core orchestration layer for LLM interactions. Coordinates context building,
prompt layered assembly, provider routing, execution, and output verification.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Any

from backend.config import get_settings
from backend.llm.context import context_manager
from backend.llm.events import Event, event_bus
from backend.llm.prompts import PromptLayers, prompt_manager
from backend.llm.router import provider_router
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Verification Hook Type: Takes the raw LLM string, returns a verified/modified string.
# Raises an Exception if verification fails critically.
VerificationHook = Callable[[str], Awaitable[str]]


class ConversationEngine:
    """Orchestrates the entire conversation pipeline."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._verification_hooks: list[VerificationHook] = []

        # Add a default basic validator hook that simply logs it
        self.add_verification_hook(self._default_verification_hook)

    def add_verification_hook(self, hook: VerificationHook) -> None:
        """Register a post-processing verification hook."""
        self._verification_hooks.append(hook)

    async def _default_verification_hook(self, output: str) -> str:
        """A simple pass-through hook for Phase 2A."""
        logger.debug("verifying_output", length=len(output))
        # In the future, we could verify JSON formatting or check for secrets here.
        return output

    async def _run_verification_pipeline(self, output: str) -> str:
        """Run the raw LLM output through all registered verification hooks."""
        verified_output = output
        for hook in self._verification_hooks:
            verified_output = await hook(verified_output)
        return verified_output

    async def process_message(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        model_override: str | None = None,
        extra_vars: dict[str, Any] | None = None,
    ) -> str:
        """Process a user message synchronously (waits for full response)."""
        logger.info("processing_message", conversation_id=conversation_id)

        # 1. Dispatch event that processing started
        event_bus.publish(
            Event(
                name="conversation.started",
                source="engine",
                payload={"conversation_id": conversation_id, "message": message},
            )
        )

        model_name = model_override or self.settings.llm_model
        provider = provider_router.get_provider_for_model(model_name)

        # 2. Build Context (Simulating DB fetch for Phase 2A, or passing just the new message)
        # In a full implementation, we'd fetch `messages` from `ConversationRepository`.
        # Here we just treat the current message as the unpinned history.
        history = [{"role": "user", "content": message}]
        trimmed_history = context_manager.build_context_window(
            model_name=model_name,
            messages=history,
            system_prompt_tokens=200,  # Estimated
        )

        # 3. Assemble Prompt
        layers = PromptLayers(
            pinned_memories=[],  # Would fetch from MemoryRepository
            tools=[],  # Would fetch from active tools
            task_context=None,
            extra_vars=extra_vars or {},
        )
        system_prompt = prompt_manager.compile_system_prompt(layers)

        # 4. Execute
        try:
            raw_response = await provider.generate(
                model=model_name,
                messages=trimmed_history,
                system_prompt=system_prompt,
            )
        except Exception as e:
            event_bus.publish(
                Event(
                    name="conversation.error",
                    source="engine",
                    payload={"conversation_id": conversation_id, "error": str(e)},
                )
            )
            raise e

        # 5. Verify
        verified_response = await self._run_verification_pipeline(raw_response)

        # 6. Dispatch completion event
        event_bus.publish(
            Event(
                name="conversation.completed",
                source="engine",
                payload={"conversation_id": conversation_id, "response": verified_response},
            )
        )

        return verified_response

    async def stream_message(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        model_override: str | None = None,
        extra_vars: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Process a user message and stream the response back token by token."""
        logger.info("streaming_message", conversation_id=conversation_id)

        model_name = model_override or self.settings.llm_model
        provider = provider_router.get_provider_for_model(model_name)

        history = [{"role": "user", "content": message}]
        trimmed_history = context_manager.build_context_window(
            model_name=model_name,
            messages=history,
            system_prompt_tokens=200,
        )

        layers = PromptLayers(
            pinned_memories=[],
            tools=[],
            task_context=None,
            extra_vars=extra_vars or {},
        )
        system_prompt = prompt_manager.compile_system_prompt(layers)

        # Note: Streaming responses bypass the full string verification pipeline initially.
        # Verification on streams is complex (usually requires buffering or windowing).
        # For Phase 2A, we yield directly.
        async for chunk in provider.stream(
            model=model_name,
            messages=trimmed_history,
            system_prompt=system_prompt,
        ):
            yield chunk


# Global singleton
conversation_engine = ConversationEngine()
