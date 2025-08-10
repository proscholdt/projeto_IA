# api/chatRouter.py
from fastapi import APIRouter, Body, Query
from pydantic import BaseModel
from services.chatService import chat_with_rag, new_session_id, reset_history

router = APIRouter()

class ChatInput(BaseModel):
    message: str
    session_id: str | None = None  # opcional

@router.post("/api/chat/message")
async def chat_message(payload: ChatInput):
    session_id = payload.session_id or new_session_id()
    result = await chat_with_rag(session_id, payload.message)
    return result

@router.post("/api/chat/reset")
async def chat_reset(session_id: str = Query(...)):
    reset_history(session_id)
    return {"ok": True}
