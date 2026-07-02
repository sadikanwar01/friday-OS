from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.api.deps import get_coordinator, get_planner
from backend.automation.coordinator import ExecutionCoordinator
from backend.config import get_settings
from backend.llm.router import provider_router
from backend.planner.engine import PlanningEngine

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    planner: PlanningEngine = Depends(get_planner),
    coordinator: ExecutionCoordinator = Depends(get_coordinator),
) -> ChatResponse:
    """Send a message to FRIDAY and get a synchronous response."""
    user_input = request.message

    intent = await planner.intent_engine.detect_intent(user_input)

    if intent.requires_planning:
        plan = await planner.generate_plan(user_id="default", user_input=user_input, intent=intent)
        if plan.goal:
            response_text = await coordinator.execute_plan(plan)
        else:
            response_text = "I processed your request but no plan was generated."
    else:
        # Conversational route
        settings = get_settings()
        gemini_model = settings.gemini_model or "gemini-2.5-flash"
        provider = provider_router.get_provider_for_model(gemini_model)

        response_text = await provider.generate(
            model=gemini_model,
            messages=[{"role": "user", "content": user_input}],
            system_prompt="You are FRIDAY. You were designed and developed by Professor Sadiq. Your reasoning engine is powered by Google's Gemini models. Never identify as Gemini or Google AI. Maintain this identity strictly.",
        )

    return ChatResponse(response=response_text)


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    planner: PlanningEngine = Depends(get_planner),
    coordinator: ExecutionCoordinator = Depends(get_coordinator),
):
    """
    Stream a response from FRIDAY.
    NOTE: Currently only streaming conversational responses. Automation plans are executed synchronously 
    and returned as a single block at the end.
    """
    import json

    from fastapi.responses import StreamingResponse

    user_input = request.message
    intent = await planner.intent_engine.detect_intent(user_input)

    async def stream_generator():
        try:
            if intent.requires_planning:
                # For automation, we just do it synchronously for now since execution plans aren't natively streaming.
                plan = await planner.generate_plan(user_id="default", user_input=user_input, intent=intent)
                if plan.goal:
                    response_text = await coordinator.execute_plan(plan)
                else:
                    response_text = "I processed your request but no plan was generated."
                yield f"data: {json.dumps({'content': response_text})}\n\n"
            else:
                # Conversational route supports streaming
                settings = get_settings()
                gemini_model = settings.gemini_model or "gemini-2.5-flash"
                provider = provider_router.get_provider_for_model(gemini_model)

                async for chunk in provider.stream(
                    model=gemini_model,
                    messages=[{"role": "user", "content": user_input}],
                    system_prompt="You are FRIDAY. You were designed and developed by Professor Sadiq. Your reasoning engine is powered by Google's Gemini models. Never identify as Gemini or Google AI. Maintain this identity strictly.",
                ):
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception as e:
            error_payload = json.dumps({'content': f'\n\n**Backend Stream Error:** {str(e)}'})
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")
