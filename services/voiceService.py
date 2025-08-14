# services/voiceService.py
import os
import base64
import tempfile
from uuid import uuid4
from typing import Any, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from services.chatService import chat_with_rag, new_session_id

load_dotenv()
client = OpenAI(api_key=os.getenv("api_key_openIA"))

_MIN_SIZE_BYTES = 2000  # evita envio de áudio vazio/curtíssimo

def _pick_suffix(mime_type: Optional[str]) -> str:
    if not mime_type:
        return ".webm"
    m = mime_type.lower()
    if "webm" in m: return ".webm"
    if "ogg" in m or "opus" in m: return ".ogg"
    if "wav" in m: return ".wav"
    if "mp3" in m or "mpeg" in m or "mpga" in m: return ".mp3"
    if "mp4" in m: return ".mp4"
    if "m4a" in m: return ".m4a"
    if "flac" in m: return ".flac"
    return ".webm"

async def talk_with_voice(
    session_id: Optional[str],
    audio_bytes: bytes,
    mime_type: Optional[str] = None,
    do_backend_tts: bool = False,
) -> Dict[str, Any]:
    """
    1) Transcreve o áudio (Whisper).
    2) Consulta o mesmo RAG do chat de texto.
    3) (Opcional) Gera áudio TTS no backend e retorna base64 (se do_backend_tts=True).
    """
    sid = session_id or new_session_id()

    # Validação rápida (evita 400 do Whisper)
    if not audio_bytes or len(audio_bytes) < _MIN_SIZE_BYTES:
        return {
            "session_id": sid,
            "transcricao": "",
            "categoria": None,
            "resposta": "Não captei sua fala (áudio muito curto). Tente falar por ~1–2 segundos.",
            "fontes": [],
            "audio_base64": None,
        }

    suffix = _pick_suffix(mime_type)
    tmp_path: Optional[Path] = None

    try:
        # Grava temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_bytes)
            tmp_path = Path(tmp.name)

        # 1) Transcreve com Whisper
        try:
            with tmp_path.open("rb") as f:
                stt = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="pt",
                )
            transcricao = getattr(stt, "text", "") or ""
        except Exception as e:
            msg = str(e)
            if "audio_too_short" in msg or "Minimum audio length" in msg:
                return {
                    "session_id": sid,
                    "transcricao": "",
                    "categoria": None,
                    "resposta": "Não captei sua fala (áudio muito curto). Tente falar por ~1–2 segundos.",
                    "fontes": [],
                    "audio_base64": None,
                }
            if "Invalid file format" in msg:
                return {
                    "session_id": sid,
                    "transcricao": "",
                    "categoria": None,
                    "resposta": "Formato de áudio não reconhecido. Tente novamente ou use Chrome/Edge.",
                    "fontes": [],
                    "audio_base64": None,
                }
            return {
                "session_id": sid,
                "transcricao": "",
                "categoria": None,
                "resposta": f"Não consegui transcrever o áudio ({msg}). Tente novamente.",
                "fontes": [],
                "audio_base64": None,
            }

        # 2) Consulta o mesmo RAG
        resposta_pack = await chat_with_rag(sid, transcricao or "")
        resposta_texto = resposta_pack.get("resposta") or ""
        audio_b64 = None

        # 3) (Opcional) TTS no backend (geralmente preferimos TTS do navegador)
        if do_backend_tts and resposta_texto:
            try:
                voice = os.getenv("TTS_VOICE", "alloy")  # ex.: alloy, verse, etc.
                mp3_path = Path(tempfile.gettempdir()) / f"tts_{uuid4().hex}.mp3"
                with client.audio.speech.with_streaming_response.create(
                    model="tts-1",
                    voice=voice,
                    input=resposta_texto,
                ) as resp:
                    resp.stream_to_file(mp3_path)
                audio_b64 = base64.b64encode(mp3_path.read_bytes()).decode("utf-8")
                try:
                    mp3_path.unlink(missing_ok=True)
                except Exception:
                    pass
            except Exception:
                audio_b64 = None  # não falha a requisição principal

        return {
            "session_id": sid,
            "transcricao": transcricao,
            "categoria": resposta_pack.get("categoria"),
            "resposta": resposta_texto,
            "fontes": resposta_pack.get("fontes", []),
            "audio_base64": audio_b64,
        }

    finally:
        if tmp_path:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
