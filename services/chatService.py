
# services/chatService.py
import os
from uuid import uuid4
from typing import Dict, List, Any
from dotenv import load_dotenv
from openai import OpenAI

from services.intentService import classificar_intencao
from services.searchService import buscar_chunks_relevantes_por_categoria

load_dotenv()
client = OpenAI(api_key=os.getenv("api_key_openIA"))

# memória simples em processo (produção: redis/db)
_MEMORY: Dict[str, List[Dict[str, str]]] = {}

def new_session_id() -> str:
    return str(uuid4())

def get_history(session_id: str) -> List[Dict[str, str]]:
    return _MEMORY.setdefault(session_id, [])

def reset_history(session_id: str):
    _MEMORY.pop(session_id, None)

def _montar_contexto(trechos: List[Dict[str, Any]]) -> str:
    """
    Formata os trechos como C1..Cn para o modelo varrer tudo sem repetir.
    """
    linhas = []
    for i, t in enumerate(trechos, start=1):
        md = t.get("metadata", {})
        titulo = (md.get("titulo") or "-").strip()
        conteudo = (md.get("content") or md.get("trecho") or "").strip()
        if conteudo:
            linhas.append(f"(C{i} • {titulo}) {conteudo}")
    return "\n".join(linhas)

def _prompt_conversacional(pergunta: str, contexto: str) -> str:
    """
    Prompt em 2 etapas (fatos → resposta) com tom de conversa
    e sugestões de follow-up baseadas no próprio contexto.
    """
    return f"""
Você é um assistente RAG conversacional. Use EXCLUSIVAMENTE o CONTEXTO (C1..Cn).
NÃO invente nada fora do contexto e NÃO cite fontes/ids na resposta (sem [C1], [Fonte], etc.).

ESTILO:
- Tom humano, cordial e profissional.
- Responda direto, mas com clareza; parágrafos curtos ou bullets.
- Se a pergunta pedir algo que não está no contexto, diga isso explicitamente.
- Ao final, se fizer sentido, sugira 2–3 "Próximos assuntos" relevantes, mas somente se estiverem no CONTEXTO.

SAÍDA EM 2 PARTES (apenas para você raciocinar; entregue ao usuário só a resposta final e as sugestões):
1) Fatos do contexto: liste pontos únicos relevantes (evite redundâncias; inclua limites/condições/pré-requisitos).
2) Resposta final (conversacional), sem citar fontes. Depois, inclua "Quer saber também sobre:" com 2–3 bullets
   de assuntos relacionados que constem no contexto — se não houver, omita a seção.

### PERGUNTA
{pergunta}

### CONTEXTO (C1..Cn)
{contexto}

### FORMATO DE ENTREGA (o que o usuário verá)
<resposta_conversacional_sem_citar_fontes>

Opcional:
Quer saber também sobre:
• <assunto 1>
• <assunto 2>
• <assunto 3>
"""

async def chat_with_rag(session_id: str, user_message: str) -> Dict[str, Any]:
    history = get_history(session_id)

    # 1) Classificar intenção da pergunta atual
    categoria = await classificar_intencao(user_message)

    # 2) Recuperar chunks dessa categoria (mais cobertura)
    trechos = buscar_chunks_relevantes_por_categoria(user_message, categoria, top_k=6)
    contexto = _montar_contexto(trechos)

    # 3) Histórico (mantém ~20 mensagens)
    trimmed_history = history[-20:]

    system_msg = {
        "role": "system",
        "content": (
            "Você é um agente de suporte RAG conversacional em pt-BR. "
            "Responda APENAS com base no contexto fornecido. "
            "Não cite fontes no texto do usuário. "
            "Se algo não estiver no contexto, diga que não há informação suficiente. "
            "Seja cordial, claro e útil."
        ),
    }

    user_with_ctx = {
        "role": "user",
        "content": _prompt_conversacional(user_message, contexto)
    }

    # 4) Chamar o modelo
    messages = [system_msg] + trimmed_history + [user_with_ctx]
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",   
        messages=messages,
        temperature=0.45,
        max_tokens=700,
    )
    answer = (resp.choices[0].message.content or "").strip()

    # 5) Atualizar memória (histórico curto)
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": answer})

    # 6) Preparar fontes para a UI (sem exibir no texto)
    fontes = [
        {
            "titulo": t["metadata"].get("titulo"),
            "categoria": t["metadata"].get("categoria"),
            "trecho": t["metadata"].get("content") or t["metadata"].get("trecho") or "",
        }
        for t in trechos
    ]

    return {
        "session_id": session_id,
        "categoria": categoria,
        "resposta": answer,
        "fontes": fontes,
    }






