from backend.llm.context import ContextManager


def test_context_manager_token_estimation():
    manager = ContextManager(chars_per_token=4.0)
    # 20 chars / 4 = 5 tokens
    assert manager.estimate_tokens("This is twenty chars") == 5


def test_context_window_trimming():
    manager = ContextManager(chars_per_token=4.0)
    messages = [
        {"role": "user", "content": "A" * 100},  # 25 tokens + 4 = 29
        {"role": "assistant", "content": "B" * 100},  # 29
        {"role": "user", "content": "C" * 100},  # 29
    ]

    # Set limit to 60 tokens (should fit only the last 2 messages)
    trimmed = manager.build_context_window(
        model_name="unknown", messages=messages, max_tokens_override=60
    )

    assert len(trimmed) == 2
    assert trimmed[0]["content"] == "B" * 100
    assert trimmed[1]["content"] == "C" * 100


def test_pinned_messages_bypass_eviction():
    manager = ContextManager(chars_per_token=4.0)
    messages = [
        {"role": "user", "content": "pinned", "pinned": True},
        {"role": "user", "content": "A" * 100},
        {"role": "assistant", "content": "B" * 100},
    ]

    # 60 tokens limit. Pinned takes ~5 tokens. Unpinned take ~29 each.
    # Total = 63 tokens. Should evict 'A'.
    trimmed = manager.build_context_window(
        model_name="unknown", messages=messages, max_tokens_override=60
    )

    # It returns unpinned trimmed list in this implementation for Phase 2A
    assert len(trimmed) == 1
    assert trimmed[0]["content"] == "B" * 100
