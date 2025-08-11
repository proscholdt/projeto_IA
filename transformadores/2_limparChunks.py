import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

# === 1. Carregar chave da OpenAI do .env ===
load_dotenv()
api_key = os.getenv("api_key_openIA")

# === 2. Inicializar cliente OpenAI ===
client = OpenAI(api_key=api_key)

# === 3. Parâmetros ===
ARQUIVO_ENTRADA = "chunks_com_metadados_ate_1000_tokens.jsonl"
ARQUIVO_SAIDA = "chunks_limpos.jsonl"
MODELO = "gpt-3.5-turbo"
TEMPERATURE = 0.0

# === 4. Função para limpar chunk com OpenAI API v1 ===
def limpar_chunk(content, categoria):
    prompt = f"""
Você é um assistente que filtra ruídos e frases sem sentido em textos técnicos.

Texto original:
\"\"\"{content}\"\"\"

Categoria: {categoria}

Remova quaisquer frases ou trechos que não façam sentido, estejam fora de contexto ou sejam ruído (ex: 'banana azul voadora', números aleatórios, frases irrelevantes). Retorne apenas o conteúdo útil e relevante.
"""
    try:
        response = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": "Você é um assistente que limpa textos técnicos."},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ Erro com a OpenAI:", e)
        return content  # fallback: retorna original

# === 5. Função de pós-processamento ===
def posprocessar(texto):
    texto = texto.strip()

    # Remover prefixos e sufixos
    texto = re.sub(r'^texto filtrado:\s*', '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'^"""\s*', '', texto)
    texto = re.sub(r'\s*"""$', '', texto)
    texto = re.sub(r'categoria:\s.*$', '', texto, flags=re.IGNORECASE)

    # Remover quebras de linha e espaços duplicados
    texto = texto.replace('\n', ' ')
    texto = re.sub(r'\s+', ' ', texto)

    # Remover barras que não estão entre números
    texto = re.sub(r'(?<!\d)/|/(?!\d)', '', texto)

    # Remover sequência específica: barra seguida de aspas (ex: \")
    texto = texto.replace('\"', '')

    return texto.strip()


# === 6. Processar o arquivo ===
with open(ARQUIVO_ENTRADA, "r", encoding="utf-8") as f_in, \
     open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f_out:

    for linha in f_in:
        registro = json.loads(linha)
        original = registro["content"]
        categoria = registro.get("categoria", "")

        print(f"🔍 Limpando chunk da categoria: {categoria}")
        texto_limpo = limpar_chunk(original, categoria)
        texto_limpo = posprocessar(texto_limpo)
        registro["content"] = texto_limpo

        f_out.write(json.dumps(registro, ensure_ascii=False) + "\n")

print(f"\n✅ Processo finalizado. Arquivo salvo: {ARQUIVO_SAIDA}")
