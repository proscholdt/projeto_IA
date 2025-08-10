import os
from openai import OpenAI

CATEGORIAS = [
    "Produtos e Serviços",
    "Política de Crédito",
    "Onboarding",
    "Segurança da Informação",
    "Compliance",
]

_client = OpenAI(api_key=os.getenv("api_key_openIA"))

async def classificar_intencao(pergunta: str) -> str:
    """
    Classifica a pergunta em uma das categorias conhecidas.
    Retorna sempre uma das strings em CATEGORIAS.
    """
    prompt = f"""
Classifique a pergunta abaixo em UMA das categorias da lista. 
Responda só com o nome EXATO da categoria.

Categorias: {CATEGORIAS}

Pergunta: "{pergunta}"
"""

    resp = _client.chat.completions.create(
        model="gpt-4o-mini",  # econômico e bom para classificação
        messages=[
            {"role": "system", "content": "Você é um classificador de intenções."},
            {"role": "user", "content": prompt}
        ]
    )

    categoria = resp.choices[0].message.content.strip()

    # fallback defensivo se vier algo fora da lista
    if categoria not in CATEGORIAS:
        # heurística simples: escolhe a mais próxima por substring
        cat_lower = categoria.lower()
        for c in CATEGORIAS:
            if c.lower() in cat_lower or cat_lower in c.lower():
                return c
        # fallback final
        return "Produtos e Serviços"
    return categoria
