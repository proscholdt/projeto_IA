

from fastapi import APIRouter
from pydantic import BaseModel
from services.ragService import gerar_resposta_com_citacoes
from services.avaliacaoService import avaliar  # sua função que já calcula métricas

router = APIRouter()

class Pergunta(BaseModel):
    pergunta: str

@router.post("/api/rag/pergunta")
async def responder_avaliar(dados: Pergunta):
    result = await gerar_resposta_com_citacoes(dados.pergunta)

    # usa os mesmos chunks que foram usados p/ responder
    chunks = [f["trecho"] for f in result["fontes"]]

    metricas = await avaliar(
        pergunta=dados.pergunta,
        resposta=result["resposta"],
        chunks=chunks
    )

    return {
        "categoria": result["categoria"],
        "resposta": result["resposta"],
        "fontes": result["fontes"],
        "avaliacao": metricas,
    }
