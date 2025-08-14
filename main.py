from fastapi import FastAPI
from api.indexRouter import router as api_index_router
from api.ragRouter import router as api_rag_router
from api.frontendRouter import router as frontend_router
from api.avaliacaoRouter import router as avaliacao_router
from api.chatRouter import router as api_chat_router
from api.vizRouter import router as api_viz_router
from api.homeRouter import router as home_router
from api.voiceRouter import router as voice_router

from fastapi.staticfiles import StaticFiles


app = FastAPI()

# Rotas
app.include_router(frontend_router)
app.include_router(api_index_router)
app.include_router(api_rag_router)
app.include_router(avaliacao_router)
app.include_router(api_chat_router)
app.include_router(api_viz_router)
app.include_router(home_router)
app.include_router(voice_router)

# Servir pasta HTML
app.mount("/html", StaticFiles(directory="HTML"), name="html")

