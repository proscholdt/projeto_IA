
from services.searchService import buscar_chunks_relevantes_por_categoria
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("api_key_openIA"))

def _montar_contexto(trechos) -> str:
    linhas = []
    for i, t in enumerate(trechos, start=1):
        meta = t["metadata"]
        titulo = meta.get("titulo") or "-"
        content = meta.get("content") or meta.get("trecho") or ""
        linhas.append(f"(C{i} • {titulo}) {content}")
    return "\n".join(linhas)

def _prompt_resposta(pergunta: str, contexto: str) -> str:
    return f"""
Você é um assistente RAG. Use EXCLUSIVAMENTE o bloco CONTEXTO (C1..Cn) para responder.
NÃO invente, NÃO traga conhecimento externo e NÃO cite fontes/rotulagens (sem [C1], [Fonte], etc.).

TAREFA EM 2 ETAPAS:
1) Fatos do contexto: liste os fatos únicos e relevantes presentes no CONTEXTO (inclua limites, condições,
   exceções, pré-requisitos e processos quando houver; remova redundâncias).
2) Resposta final: componha uma resposta clara e completa para a PERGUNTA:
   - Comece com 2–4 linhas de resumo objetivo.
   - Depois traga bullets/tópicos práticos (3–8 itens) cobrindo os pontos relevantes do CONTEXTO.
   - Se algo pedido na pergunta NÃO estiver no CONTEXTO, diga explicitamente:
     "Não há informação suficiente no contexto para <X>".

REGRAS:
- Varra TODOS os trechos do CONTEXTO e incorpore os pontos não repetidos.
- Não repita o mesmo item.
- Linguagem simples, profissional, pt-BR.
- Sem citações de fonte na resposta.

### PERGUNTA
{pergunta}

### CONTEXTO (C1..Cn)
{contexto}

### SAÍDA
1) Fatos do contexto
- ...

2) Resposta final
Resumo: ...
• ...
• ...
• ...
"""

async def gerar_resposta_com_citacoes(pergunta: str):
    from services.intentService import classificar_intencao
    categoria = await classificar_intencao(pergunta)

    # top_k ↑ para dar mais cobertura
    trechos = buscar_chunks_relevantes_por_categoria(pergunta, categoria, top_k=6)

    contexto = _montar_contexto(trechos)
    prompt = _prompt_resposta(pergunta, contexto)

    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",   # troque se quiser (ex.: gpt-4o-mini)
        messages=[
            {"role": "system", "content": "Responda APENAS com base no CONTEXTO. Não invente e não cite fontes."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.45,
        max_tokens=650
    )

    resposta_modelo = resp.choices[0].message.content.strip()

    fontes = [
        {
            "titulo": t["metadata"].get("titulo"),
            "categoria": t["metadata"].get("categoria"),
            "trecho": t["metadata"].get("content") or t["metadata"].get("trecho") or ""
        }
        for t in trechos
    ]

    return {
        "categoria": categoria,
        "resposta": resposta_modelo,  # texto sem citar fontes
        "fontes": fontes              # mostradas na aba "Fontes" da sua UI
    }
