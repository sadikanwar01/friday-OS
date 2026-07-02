from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.api.deps import get_voice_manager
from backend.voice.pipeline import VoiceSessionManager

router = APIRouter(prefix="/api/voice", tags=["voice"])


class VoiceRequest(BaseModel):
    action: str  # "start_listening", "stop_listening", "synthesize"
    text: str | None = None


class VoiceResponse(BaseModel):
    status: str
    message: str | None = None


@router.post("", response_model=VoiceResponse)
async def manage_voice(
    request: VoiceRequest,
    voice_manager: VoiceSessionManager = Depends(get_voice_manager),
) -> VoiceResponse:
    """Trigger voice pipeline actions manually."""
    if request.action == "start_listening":
        # In a real environment, this triggers PyAudio recording.
        # Since it's headless, it's just state management.
        return VoiceResponse(status="listening")
    elif request.action == "stop_listening":
        return VoiceResponse(status="stopped")
    elif request.action == "synthesize" and request.text:
        audio = await voice_manager.tts.synthesize(request.text)
        voice_manager.speaker.play_audio(audio)
        return VoiceResponse(status="playing", message="Synthesizing audio")

    return VoiceResponse(status="error", message="Unknown action")
