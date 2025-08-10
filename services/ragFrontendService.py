from services.searchService import buscar_chunks_relevantes
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("api_key_openIA"))

def responder_simples(pergunta: str) -> str:
    trechos = buscar_chunks_relevantes(pergunta)

    if not trechos:
        return "❌ Resposta não encontrada."

    contexto = "\n\n".join(
        f"[Fonte {i+1} - {t.metadata.get('titulo')}]: {t.metadata.get('content')}"
        for i, t in enumerate(trechos)
    )

    prompt = f"""
Você é um assistente inteligente. Com base nas fontes abaixo, responda à pergunta do usuário com precisão e clareza.

Fontes:
{contexto}

Pergunta: {pergunta}
Resposta:
"""

    resposta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente que responde com base em documentos técnicos."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return resposta.choices[0].message.content.strip()
