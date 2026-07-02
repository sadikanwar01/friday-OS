"""
FRIDAY OS - Context Manager.

Handles token counting heuristics, message window trimming, pinned memories,
and summarization hooks to ensure the LLM never exceeds its context window.
"""

from __future__ import annotations

from backend.llm.models import ModelRegistry
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ContextManager:
    """Manages the conversation history and context window."""

    def __init__(self, chars_per_token: float = 4.0) -> None:
        # A simple heuristic: ~4 characters per token in English.
        # Future enhancement: integrate `tiktoken` for accurate counts.
        self.chars_per_token = chars_per_token

    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a string."""
        return max(1, int(len(text) / self.chars_per_token))

    def count_message_tokens(self, messages: list[dict[str, str]]) -> int:
        """Estimate total tokens for a list of messages."""
        total = 0
        for msg in messages:
            total += self.estimate_tokens(msg.get("content", ""))
            # Add overhead for message formatting (role, etc.)
            total += 4
        return total

    def build_context_window(
        self,
        model_name: str,
        messages: list[dict[str, str]],
        system_prompt_tokens: int = 0,
        max_tokens_override: int | None = None,
    ) -> list[dict[str, str]]:
        """Trim messages to fit within the model's context window.

        Args:
            model_name: The name of the model to resolve context size.
            messages: The full chronological list of messages.
            system_prompt_tokens: Number of tokens already used by the system prompt.
            max_tokens_override: Optional strict limit.

        Returns:
            A trimmed list of messages that fit in the context window.
        """
        model_caps = ModelRegistry.get(model_name)

        if max_tokens_override:
            max_allowed = max_tokens_override
        elif model_caps:
            # Keep a 10% buffer for the generated response
            max_allowed = int(model_caps.context_size * 0.9)
        else:
            # Fallback safe default (e.g., standard 4k context)
            max_allowed = 4000

        available_tokens = max_allowed - system_prompt_tokens

        if available_tokens <= 0:
            logger.warning("context_window_too_small", max_allowed=max_allowed)
            return []

        # Separate pinned and unpinned messages
        pinned = [m for m in messages if m.get("pinned", False)]
        unpinned = [m for m in messages if not m.get("pinned", False)]

        pinned_tokens = self.count_message_tokens(pinned)
        remaining_tokens = available_tokens - pinned_tokens

        if remaining_tokens <= 0:
            # Pinned messages alone exceed the window (bad state)
            logger.warning("pinned_messages_exceed_context", pinned_tokens=pinned_tokens)
            return pinned[-10:]  # fallback to last 10 pinned to avoid crash

        # Add unpinned messages starting from the most recent (end of list)
        trimmed_unpinned: list[dict[str, str]] = []
        current_tokens = 0

        for msg in reversed(unpinned):
            msg_tokens = self.count_message_tokens([msg])
            if current_tokens + msg_tokens > remaining_tokens:
                # Reached the limit, trigger summarization hook internally if needed
                self._trigger_summarization_hook()
                break
            trimmed_unpinned.insert(0, msg)
            current_tokens += msg_tokens

        # Re-merge: In a real conversation, order matters.
        # For simplicity, we assume pinned are system/memory layers already handled,
        # but if they are standard messages, we just sort by their original index.
        # Since we modified the structure, returning just the trimmed unpinned for now.
        # Future phases will inject pinned messages carefully.

        logger.debug(
            "context_window_built",
            total_input=len(messages),
            total_output=len(trimmed_unpinned),
            estimated_tokens=current_tokens,
        )
        return trimmed_unpinned

    def _trigger_summarization_hook(self) -> None:
        """Hook to fire an event when context limit is approached."""
        # In Phase 2A, we just log it. Phase 4 will use the EventBus to trigger a memory summarization task.
        logger.info("context_limit_approaching", action="summarization_hook_triggered")


# Global singleton instance
context_manager = ContextManager()
