
from typing import List, Optional, Dict, Any
import os
from openai import OpenAI
from pinecone import Pinecone

OPENAI_API_KEY = os.getenv("api_key_openIA")
PINECONE_API_KEY = os.getenv("api_key_pinecone")
INDEX_NAME = "testeanalistasr"

_openai = OpenAI(api_key=OPENAI_API_KEY)
_pc = Pinecone(api_key=PINECONE_API_KEY)
_index = _pc.Index(INDEX_NAME)

def _embed(texto: str) -> List[float]:
    resp = _openai.embeddings.create(
        model="text-embedding-3-small",
        input=texto
    )
    return resp.data[0].embedding

def _normalizar_matches(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
    matches = []
    for m in (resp.get("matches") or []):
        md = m.get("metadata", {}) or {}
        matches.append({
            "id": m.get("id"),
            "score": m.get("score"),
            "metadata": {
                "titulo": md.get("titulo", ""),
                "categoria": md.get("categoria", ""),
                "content": md.get("content", ""),
            }
        })
    return matches

def buscar_chunks_relevantes_por_categoria(
    pergunta: str,
    categoria: str,
    top_k: int = 4
) -> List[Dict[str, Any]]:
    """
    Busca no Pinecone filtrando por categoria no metadata.
    Retorna lista normalizada:
    [
      {
        "id": <str>,
        "score": <float>,
        "metadata": {"titulo":..., "categoria":..., "content":...}
      },
      ...
    ]
    """
    emb = _embed(pergunta)
    resp = _index.query(
        vector=emb,
        top_k=top_k,
        include_metadata=True,
        filter={"categoria": {"$eq": categoria}}
    )
    return _normalizar_matches(resp)

def buscar_chunks_relevantes(
    pergunta: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Busca sem filtro de categoria. Retorno normalizado igual ao acima.
    """
    emb = _embed(pergunta)
    resp = _index.query(
        vector=emb,
        top_k=top_k,
        include_metadata=True
    )
    return _normalizar_matches(resp)
