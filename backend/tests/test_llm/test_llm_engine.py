import pytest

from backend.llm.engine import ConversationEngine


@pytest.mark.asyncio
async def test_conversation_engine_verification_pipeline():
    engine = ConversationEngine()

    async def dummy_hook(output: str) -> str:
        return output.replace("bad", "good")

    engine.add_verification_hook(dummy_hook)

    result = await engine._run_verification_pipeline("This is a bad output.")
    assert result == "This is a good output."
