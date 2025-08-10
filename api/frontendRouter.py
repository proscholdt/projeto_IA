from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse
import os
from services.frontendService import servir_html_avaliacao_auto

router = APIRouter()


@router.get("/avaliacao-auto")
def frontend_avaliacao():
    return servir_html_avaliacao_auto()

@router.get("/avaliacao-seq")
def frontend_avaliacao_seq():
    caminho = os.path.join(os.path.dirname(__file__), "..", "html", "avaliacao_seq.html")
    return FileResponse(os.path.abspath(caminho))

@router.get("/chatbot")
def chatbot_page():
    path = os.path.join(os.path.dirname(__file__), "..", "html", "chat.html")
    return FileResponse(os.path.abspath(path))

@router.get("/wa")
def wa_dashboard():
    path = os.path.join(os.path.dirname(__file__), "..", "html", "wa_dashboard.html")
    return FileResponse(os.path.abspath(path))
