from backend.llm.prompts import PromptLayers, PromptManager


def test_prompt_manager_compilation():
    manager = PromptManager()

    class DummyTool:
        name = "search"
        description = "Search the web"

    layers = PromptLayers(
        pinned_memories=["User prefers dark mode.", "User is a developer."],
        tools=[DummyTool()],
        task_context="Analyze this python file.",
    )

    result = manager.compile_system_prompt(layers)

    assert "You are FRIDAY" in result
    assert "User prefers dark mode." in result
    assert "Search the web" in result
    assert "Analyze this python file." in result
