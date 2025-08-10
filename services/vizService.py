# services/vizService.py
import os
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.decomposition import PCA
from openai import OpenAI
from pinecone import Pinecone

OPENAI_API_KEY = os.getenv("api_key_openIA")
PINECONE_API_KEY = os.getenv("api_key_pinecone")
INDEX_NAME = "testeanalistasr"

_openai = OpenAI(api_key=OPENAI_API_KEY)
_pc = Pinecone(api_key=PINECONE_API_KEY)
_index = _pc.Index(INDEX_NAME)

def _embed(texts: List[str]) -> List[List[float]]:
    resp = _openai.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [d.embedding for d in resp.data]

def _top_chunks(pergunta: str, top_k: int = 8) -> List[Dict[str, Any]]:
    vec = _embed([pergunta])[0]
    res = _index.query(vector=vec, top_k=top_k, include_metadata=True)
    matches = []
    for m in (res.get("matches") or []):
        md = m.get("metadata", {}) or {}
        matches.append({
            "id": m.get("id"),
            "score": m.get("score"),
            "categoria": md.get("categoria", ""),
            "titulo": md.get("titulo", ""),
            "content": md.get("content", ""),
        })
    return matches

def _cosine_sim_matrix(X: np.ndarray) -> np.ndarray:
    # X shape: (n, d)
    # normalize
    norms = np.linalg.norm(X, axis=1, keepdims=True) + 1e-9
    Xn = X / norms
    return np.dot(Xn, Xn.T)

def project_space(pergunta: str, resposta: str | None, top_k: int = 8) -> Dict[str, Any]:
    """Retorna pontos projetados em 2D (PCA) e metadados para scatter."""
    chunks = _top_chunks(pergunta, top_k=top_k)

    textos = [f"PERGUNTA: {pergunta}"]
    tipos  = ["pergunta"]
    grupos = ["pergunta"]
    cats   = ["Pergunta"]
    titulos= ["Pergunta"]

    if resposta:
        textos.append(f"RESPOSTA: {resposta}")
        tipos.append("resposta")
        grupos.append("resposta")
        cats.append("Resposta")
        titulos.append("Resposta")

    for c in chunks:
        textos.append(c["content"])
        tipos.append("chunk")
        grupos.append(c.get("categoria") or "Chunk")
        cats.append(c.get("categoria") or "Chunk")
        titulos.append(c.get("titulo") or "Chunk")

    embs = np.array(_embed(textos))

    # PCA para 2D
    pca = PCA(n_components=2)
    pts = pca.fit_transform(embs)   # shape (n, 2)

    out = []
    for i in range(len(textos)):
        out.append({
            "x": float(pts[i, 0]),
            "y": float(pts[i, 1]),
            "tipo": tipos[i],          # pergunta/resposta/chunk
            "grupo": grupos[i],        # categoria p/ chunk, ou "pergunta"/"resposta"
            "categoria": cats[i],
            "titulo": titulos[i],
            "texto": textos[i],
        })

    return {
        "points": out,
        "explained_variance": [float(v) for v in pca.explained_variance_ratio_]
    }

def build_heatmap(pergunta: str, resposta: str | None, top_k: int = 8) -> Dict[str, Any]:
    """Retorna matriz de similaridade e rótulos para heatmap."""
    chunks = _top_chunks(pergunta, top_k=top_k)

    labels = ["Pergunta"]
    textos = [pergunta]

    if resposta:
        labels.append("Resposta")
        textos.append(resposta)

    for c in chunks:
        labels.append(f"{c.get('categoria','')}: {c.get('titulo','')}".strip(": "))
        textos.append(c["content"])

    embs = np.array(_embed(textos))
    sim = _cosine_sim_matrix(embs)   # (n x n)

    return {
        "labels": labels,
        "matrix": sim.tolist()
    }
