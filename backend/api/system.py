import psutil
from fastapi import APIRouter
from pydantic import BaseModel

from backend.config import get_settings

router = APIRouter(prefix="/api/system", tags=["system"])


class SystemStatusResponse(BaseModel):
    cpu_percent: float
    ram_percent: float
    gemini_status: str
    memory_status: str
    automation_status: str
    voice_status: str


@router.get("", response_model=SystemStatusResponse)
async def get_system_status() -> SystemStatusResponse:
    """Get system telemetry and internal module statuses."""
    # Since modules are running in memory, their status is effectively online if we reach here
    settings = get_settings()
    gemini_status = "online" if settings.gemini_api_key else "missing_key"

    return SystemStatusResponse(
        cpu_percent=psutil.cpu_percent(),
        ram_percent=psutil.virtual_memory().percent,
        gemini_status=gemini_status,
        memory_status="online",
        automation_status="online",
        voice_status="mock" if settings.app_env == "test" else "online"
    )
