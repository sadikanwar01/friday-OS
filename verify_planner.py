import asyncio
import json
from unittest.mock import AsyncMock, patch

from backend.memory.manager import MemoryManager
from backend.planner.engine import PlanningEngine


async def main():
    print("Starting Planner System Verification (Phase 2C)...")

    # Mock MemoryManager to return an empty context
    mock_memory = AsyncMock(spec=MemoryManager)
    mock_memory.search.return_value = []

    engine = PlanningEngine(mock_memory)

    # We will patch provider_router to return mock structured JSON
    # to avoid needing a live local LLM for this verification script.
    mock_intent_json = {
        "primary_intent": "build_website",
        "complexity": "high",
        "requires_planning": True
    }

    mock_plan_json = {
        "plan_version": "1.0",
        "planner_version": "1.0.0",
        "goal": "Build a React website and deploy it",
        "steps": [
            {
                "id": "step_1",
                "name": "Init Repo",
                "description": "Initialize Vite React app.",
                "dependencies": [],
                "assigned_agent": "coder"
            },
            {
                "id": "step_2",
                "name": "Deploy",
                "description": "Deploy to Vercel.",
                "dependencies": ["step_1"],
                "assigned_agent": "automation"
            }
        ],
        "required_tools": ["npx", "git"],
        "required_memory": ["Vercel API Key"],
        "dependencies": ["Node.js"],
        "risks": [
            {
                "description": "Deployment fails",
                "severity": "medium",
                "mitigation": "Check build logs locally first."
            }
        ],
        "confidence_score": 0.95,
        "confidence_reason": "Standard web development workflow.",
        "verification_strategy": "Check URL returns 200.",
        "retry_strategy": "Retry deployment step 3 times.",
        "expected_output": "A live URL to the website."
    }

    # Patch the LLM Provider at the router level
    with patch("backend.planner.intent.provider_router") as mock_intent_router, \
         patch("backend.planner.engine.provider_router") as mock_engine_router:

        mock_provider = AsyncMock()
        mock_provider.generate.side_effect = [
            json.dumps(mock_intent_json),  # Called by IntentDetectionEngine
            json.dumps(mock_plan_json)     # Called by PlanningEngine
        ]
        mock_intent_router.get_provider_for_model.return_value = mock_provider
        mock_engine_router.get_provider_for_model.return_value = mock_provider

        print("\n[Test 1] Executing Hybrid Planning Pipeline...")
        plan = await engine.generate_plan("user_1", "Build a React website and deploy it")

        print("\n  -> Pipeline Execution Successful!")
        print(f"  -> Generated Plan Goal: {plan.goal}")
        print(f"  -> Total Steps: {len(plan.steps)}")
        print(f"  -> Confidence Score: {plan.confidence_score} ({plan.confidence_reason})")
        print(f"  -> Step 1: {plan.steps[0].name} - {plan.steps[0].description}")
        print(f"  -> Step 2: {plan.steps[1].name} (Depends on: {plan.steps[1].dependencies[0]})")

    print("\nVerification Complete! The Planner components are correctly orchestrated.")


if __name__ == "__main__":
    asyncio.run(main())
