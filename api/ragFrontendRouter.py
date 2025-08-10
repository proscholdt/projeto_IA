from fastapi import APIRouter, Request
from services.ragFrontendService import responder_simples

router = APIRouter()

@router.post("/api/rag/frontend")
async def responder_frontend(request: Request):
    body = await request.json()
    pergunta = body.get("pergunta")

    if not pergunta:
        return {"resposta": "❌ Nenhuma pergunta fornecida."}

    try:
        resposta = responder_simples(pergunta)
        return {"resposta": resposta}
    except Exception as e:
        return {"resposta": f"❌ Erro ao gerar resposta: {str(e)}"}
