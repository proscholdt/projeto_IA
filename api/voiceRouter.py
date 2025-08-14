# api/voiceRouter.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import os
from services.voiceService import talk_with_voice

router = APIRouter()

@router.get("/chat-voz")
def voice_page():
    path = os.path.join(os.path.dirname(__file__), "..", "html", "voice.html")
    return FileResponse(os.path.abspath(path))

@router.post("/api/voice/talk")
async def voice_talk(
    audio: UploadFile = File(...),
    session_id: str | None = Form(None),
):
    try:
        blob = await audio.read()

        # Permite ativar TTS no backend via .env (opcional)
        use_server_tts = os.getenv("USE_SERVER_TTS", "false").lower() == "true"

        out = await talk_with_voice(
            session_id=session_id,
            audio_bytes=blob,
            mime_type=audio.content_type,
            do_backend_tts=use_server_tts,
        )
        return out
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Falha ao processar áudio: {e}")
