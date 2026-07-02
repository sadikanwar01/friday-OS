from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.api.deps import get_automation_engine
from backend.automation.engine import AutomationEngine

router = APIRouter(prefix="/api/browser", tags=["browser"])


class BrowserRequest(BaseModel):
    action: str
    url: str | None = None
    selector: str | None = None
    text: str | None = None


class BrowserResponse(BaseModel):
    success: bool
    output: str | None = None
    error: str | None = None


@router.post("", response_model=BrowserResponse)
async def execute_browser_action(
    request: BrowserRequest,
    engine: AutomationEngine = Depends(get_automation_engine),
) -> BrowserResponse:
    """Execute a browser automation action directly."""
    kwargs = {}
    if request.url:
        kwargs["url"] = request.url
    if request.selector:
        kwargs["selector"] = request.selector
    if request.text:
        kwargs["text"] = request.text

    # Auto-approve for API usage since the frontend user clicked it
    engine.safety_layer.permission_manager.approve_action("browser", request.action, kwargs)

    result = await engine.execute_tool("browser", request.action, **kwargs)
    return BrowserResponse(
        success=result.success,
        output=result.output,
        error=result.error
    )
