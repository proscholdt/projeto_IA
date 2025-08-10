# api/vizRouter.py
from fastapi import APIRouter
from pydantic import BaseModel
from services.vizService import project_space, build_heatmap

router = APIRouter()

class VizInput(BaseModel):
    pergunta: str
    resposta: str | None = None
    top_k: int = 8

@router.post("/api/viz/space")
def viz_space(payload: VizInput):
    return project_space(pergunta=payload.pergunta, resposta=payload.resposta, top_k=payload.top_k)

@router.post("/api/viz/heatmap")
def viz_heatmap(payload: VizInput):
    return build_heatmap(pergunta=payload.pergunta, resposta=payload.resposta, top_k=payload.top_k)
