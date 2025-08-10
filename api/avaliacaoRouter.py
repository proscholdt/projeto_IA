from fastapi import APIRouter, Request
from services.avaliacaoService import avaliar

router = APIRouter()

@router.post("/api/rag/avaliar")
async def avaliar_respostas(request: Request):
    body = await request.json()
    avaliacoes_input = body.get("avaliacoes", [])

    resultados = []

    for a in avaliacoes_input:
        resultado = await avaliar(
            pergunta=a["pergunta"],
            resposta=a["resposta"]
        )
        resultados.append({
            "pergunta": a["pergunta"],
            "resposta": a["resposta"],
            "precisao": resultado["precisao"],
            "cobertura": resultado["cobertura"],
            "recall3": resultado["recall3"],
            "justificativa": resultado["justificativa"],
            "fontes": resultado["fontes"]
        })

    # Calcular médias
    total = len(resultados)
    media_precisao = sum(r["precisao"] for r in resultados) / total
    media_cobertura = sum(r["cobertura"] for r in resultados) / total
    media_recall = sum(r["recall3"] for r in resultados) / total

    return {
        "metricas": {
            "mediaPrecisao": round(media_precisao, 2),
            "mediaCobertura": round(media_cobertura, 2),
            "mediaRecall": round(media_recall, 2)
        },
        "avaliacoes": resultados
    }
