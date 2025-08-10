
from openai import OpenAI
from pinecone import Pinecone
import os
import re
import json

# === Configurações ===
OPENAI_API_KEY = os.getenv("api_key_openIA")
PINECONE_API_KEY = os.getenv("api_key_pinecone")
INDEX_NAME = "testeanalistasr"

# === Inicialização ===
openai_client = OpenAI(api_key=OPENAI_API_KEY)
pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
index = pinecone_client.Index(INDEX_NAME)

# === Embedding da pergunta ===
def embed_query(query: str) -> list:
    resp = openai_client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )
    return resp.data[0].embedding

# === Busca os chunks mais relevantes (top_k maior para reduzir falso negativo) ===
def buscar_top_chunks(embedding: list, top_k: int = 5) -> list:
    """
    Retorna uma lista de strings (conteúdo) dos top_k chunks mais relevantes.
    Garante pelo menos 3 posições (preenche com string vazia se necessário).
    """
    resp = index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True
    )
    matches = resp.get("matches", []) if isinstance(resp, dict) else getattr(resp, "matches", [])
    chunks = []
    for m in matches:
        md = m.get("metadata", {}) if isinstance(m, dict) else getattr(m, "metadata", {}) or {}
        chunks.append(md.get("content", ""))

    # garante pelo menos 3
    while len(chunks) < 3:
        chunks.append("")
    return chunks[:top_k]

# === Avaliação com GPT-5 (sem temperature), exigindo JSON com evidências ===
def avaliar_resposta(pergunta: str, resposta: str, chunks: list) -> str:
    """
    Monta um prompt que:
    - Rotula os chunks como [C1], [C2], ...
    - Obriga a saída do modelo em JSON contendo evidências por afirmação.
    Retorna a string bruta da IA (para ser parseada depois).
    """
    # garante pelo menos 3 posições para recall@3 fazer sentido
    while len(chunks) < 3:
        chunks.append("")

    # rotula os chunks
    rotulados = [f"[C{i+1}] {c}" for i, c in enumerate(chunks)]
    contexto = "\n\n".join(rotulados)

    prompt = f"""
Você é um avaliador de respostas RAG. Avalie usando SOMENTE os chunks abaixo.

REGRAS IMPORTANTES:
- Se uma afirmação da resposta aparecer em QUALQUER chunk, marque como "suportado" e cite o(s) ID(s) [C#].
- NÃO marque "nao_encontrado" se a informação existir em algum chunk.
- Se houver contradição, marque "contradito" e cite as evidências.
- Cada afirmação relevante deve ter status e evidência.

Devolva APENAS JSON válido, neste formato:
{{
  "precisao": 0-10,
  "cobertura": 0-10,
  "recall3": 0-10,
  "justificativa": "texto curto",
  "evidencias": [
    {{
      "trecho_resposta": "string",
      "status": "suportado|contradito|nao_encontrado",
      "chunks_citados": ["C1","C3"],
      "evidencia": "trecho literal copiado do(s) chunk(s)"
    }}
  ]
}}

Definições:
- Precisão: quão correta está a resposta vs. os chunks.
- Cobertura: o quanto a resposta cobre os pontos relevantes dos chunks.
- Recall@3: quão bem a resposta aproveita os 3 principais trechos.

### Pergunta
{pergunta}

### Resposta
{resposta}

### Chunks
{contexto}
"""

    # gpt-5: usar default; não enviar temperature != 1
    resp = openai_client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "Você avalia respostas RAG e SEMPRE cita chunks [C#] como evidência. Devolva somente JSON."},
            {"role": "user", "content": prompt}
        ]
    )
    return resp.choices[0].message.content

# === Parser do retorno da IA, com fallback e “regra de segurança” opcional ===
def extrair_metricas(avaliacao_str: str, chunks: list) -> dict:
    """
    Tenta ler JSON estrito. Se falhar, aplica fallback por regex.
    Retorna dicionário com: precisao, cobertura, recall3, justificativa, fontes (chunks), evidencias.
    """
    # 1) tenta JSON
    try:
        data = json.loads(avaliacao_str)
        out = {
            "precisao": int(data.get("precisao", 0)),
            "cobertura": int(data.get("cobertura", 0)),
            "recall3": int(data.get("recall3", 0)),
            "justificativa": str(data.get("justificativa", "")).strip(),
            "fontes": chunks,
            "evidencias": data.get("evidencias", [])
        }
    except Exception:
        # 2) fallback por regex (se a IA escorregar do JSON)
        precisao = cobertura = recall = 0
        justificativa = ""
        evidencias = []

        m = re.search(r"(?i)Precis[aã]o.*?(\d+)", avaliacao_str)
        if m: precisao = int(m.group(1))

        m = re.search(r"(?i)Cobertura.*?(\d+)", avaliacao_str)
        if m: cobertura = int(m.group(1))

        m = re.search(r"(?i)Recall.*?(\d+)", avaliacao_str)
        if m: recall = int(m.group(1))

        m = re.search(r"(?i)justificativa.*?:\s*(.+)", avaliacao_str)
        if m: justificativa = m.group(1).strip()

        out = {
            "precisao": precisao,
            "cobertura": cobertura,
            "recall3": recall,
            "justificativa": justificativa,
            "fontes": chunks,
            "evidencias": evidencias
        }

    # 3) (Opcional) “regra de segurança” para evitar falso negativo comum
    #    Exemplo: se "bureaus externos" aparece em algum chunk e também na justificativa
    #    marcando como "não suportado", reforce na justificativa que há evidência.
    texto_unido = " ".join(chunks).lower()
    if ("bureaus extern" in texto_unido) and ("bureaus" in out.get("justificativa", "").lower()):
        out["justificativa"] += " Evidência confirmada nos chunks sobre 'bureaus externos'."

    return out

# === Função principal reutilizável ===
async def avaliar(pergunta: str, resposta: str, chunks: list) -> dict:
    """
    - Se 'chunks' já vierem do seu fluxo RAG, use-os.
    - Caso deseje avaliar com novos top-k, você pode recalcular embedding e buscar aqui.
    """
    avaliacao_str = avaliar_resposta(pergunta, resposta, chunks)
    return extrair_metricas(avaliacao_str, chunks)




