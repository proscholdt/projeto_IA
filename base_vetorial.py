import os
import json
import openai
from tqdm import tqdm
from dotenv import load_dotenv
from services.authenticationService import autentication_pinecone

# === 1. Carregar variáveis de ambiente ===
load_dotenv()
openai.api_key = os.getenv("api_key_openIA")

# === 2. Inicializar cliente Pinecone ===
pc = autentication_pinecone()
INDEX_NAME = "testeanalistasr"
index = pc.Index(INDEX_NAME)

# === 3. Carregar chunks do JSONL ===
ARQUIVO_JSONL = "chunks_limpos.jsonl"
with open(ARQUIVO_JSONL, "r", encoding="utf-8") as f:
    chunks = [json.loads(linha) for linha in f]

# === 4. Função para gerar embedding ===
def gerar_embedding(texto):
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=texto
    )
    return response.data[0].embedding

# === 5. Processar e enviar em lotes ===
BATCH_SIZE = 50
lote = []

for i, chunk in enumerate(tqdm(chunks, desc="🔁 Enviando para Pinecone")):
    texto = chunk["content"].replace('"', '').strip()
    embedding = gerar_embedding(texto)

    vetor = {
        "id": chunk["id"],
        "values": embedding,
        "metadata": {
            "titulo": chunk["titulo"],
            "categoria": chunk["categoria"],
            "content": texto  # ✅ agora salvamos o conteúdo original
        }
    }

    lote.append(vetor)

    if len(lote) == BATCH_SIZE or i == len(chunks) - 1:
        index.upsert(vectors=lote)
        lote = []

print("✅ Vetores enviados com sucesso para o índice:", INDEX_NAME)
