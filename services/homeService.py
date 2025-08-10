import os
from fastapi.responses import FileResponse

def get_home_page():
    caminho = os.path.join("HTML", "index.html")
    return FileResponse(caminho)
