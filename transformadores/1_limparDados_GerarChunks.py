import os
import re
import json
from uuid import uuid4
from nltk.tokenize import sent_tokenize
from unidecode import unidecode
import tiktoken
import nltk

# Baixar tokenizer de frases 
nltk.download('punkt')

# Inicializar tokenizer do modelo da OpenAI
tokenizer = tiktoken.get_encoding("cl100k_base")

def contar_tokens(texto):
    return len(tokenizer.encode(texto))

def limpar_texto(texto):
    texto = unidecode(texto)
    texto = texto.lower()
    texto = re.sub(r"http\S+", "", texto)
    texto = re.sub(r"[^a-zA-Z0-9\s.,;:!?()]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def extrair_metadados_e_conteudo(texto):
    linhas = texto.strip().splitlines()
    titulo = ""
    categoria = ""
    corpo = []

    for linha in linhas:
        linha = linha.strip()
        if linha.lower().startswith("título:") or linha.lower().startswith("titulo:"):
            titulo = linha.split(":", 1)[1].strip()
        elif linha.lower().startswith("categoria:"):
            categoria = linha.split(":", 1)[1].strip()
        elif linha and not re.search(r"\blorem ipsum\b", linha, re.IGNORECASE):
            corpo.append(linha)

    texto_corpo = " ".join(corpo)
    return titulo, categoria, texto_corpo

def dividir_em_chunks(texto, max_tokens=1000):
    texto_limpo = limpar_texto(texto)
    sentencas = sent_tokenize(texto_limpo)

    chunks = []
    chunk_atual = ""
    for sentenca in sentencas:
        temp_chunk = chunk_atual + " " + sentenca
        if contar_tokens(temp_chunk) <= max_tokens:
            chunk_atual = temp_chunk
        else:
            if chunk_atual:
                chunks.append(chunk_atual.strip())
            chunk_atual = sentenca
    if chunk_atual:
        chunks.append(chunk_atual.strip())
    return chunks

def processar_pasta(pasta_entrada, caminho_saida_jsonl):
    jsonl_final = []

    for nome_arquivo in os.listdir(pasta_entrada):
        if nome_arquivo.endswith(".txt"):
            caminho_arquivo = os.path.join(pasta_entrada, nome_arquivo)
            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                texto = f.read()

            titulo, categoria, corpo = extrair_metadados_e_conteudo(texto)
            if not corpo.strip():
                continue

            chunks = dividir_em_chunks(corpo)

            for chunk in chunks:
                jsonl_final.append({
                    "id": str(uuid4()),
                    "titulo": titulo,
                    "categoria": categoria,
                    "content": chunk
                })

    with open(caminho_saida_jsonl, "w", encoding="utf-8") as f_out:
        for item in jsonl_final:
            f_out.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ Gerado: {caminho_saida_jsonl} com {len(jsonl_final)} chunks")

# 🔧 Execute o processamento
processar_pasta("documentos", "chunks_com_metadados_ate_1000_tokens.jsonl")
