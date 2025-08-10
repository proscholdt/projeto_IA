def calcular_metricas(respostas):
    """
    respostas: lista de dicionários no formato:
    {
        "pergunta": "Qual é a política de segurança?",
        "resposta": "A política de segurança define...",
        "referencias_utilizadas": ["doc1", "doc3", "doc4"],
        "respostas_esperadas": ["doc3", "doc4"],
        "correta": True,
        "cobertura_semantica": 4  # de 1 a 5
    }
    """

    total_perguntas = len(respostas)

    # --- Precisão percebida ---
    total_corretas = sum(1 for r in respostas if r.get("correta") is True)
    precisao_percebida = total_corretas / total_perguntas if total_perguntas else 0

    # --- Nível de cobertura semântica ---
    cobertura_media = sum(r.get("cobertura_semantica", 0) for r in respostas) / total_perguntas if total_perguntas else 0

    # --- Recall@3 ---
    acertos_recall3 = 0
    for r in respostas:
        refs_utilizadas = set(r.get("referencias_utilizadas", [])[:3])
        refs_esperadas = set(r.get("respostas_esperadas", []))
        if refs_utilizadas & refs_esperadas:
            acertos_recall3 += 1
    recall3 = acertos_recall3 / total_perguntas if total_perguntas else 0

    return {
        "precisao_percebida": round(precisao_percebida, 2),
        "cobertura_semantica": round(cobertura_media, 2),
        "recall@3": round(recall3, 2)
    }
