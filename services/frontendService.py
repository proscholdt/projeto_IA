import os
from fastapi.responses import HTMLResponse

def servir_html_frontend():
    caminho_html = os.path.join(os.path.dirname(__file__), "..", "html", "rag_frontend.html")
    with open(os.path.abspath(caminho_html), "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)
    
def servir_html_avaliacao_auto():
    caminho = os.path.join("html", "avaliacao_auto.html")
    with open(caminho, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())
