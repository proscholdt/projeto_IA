from fastapi import APIRouter
from services.indexService import create_index, list_index, detail_index

router = APIRouter()

@router.post('/api/index/create', summary="Criar um Index")
async def create_index_router(name_index: str):
    response = create_index(name=name_index)
    return {"message": f"O index {response} foi criado com sucesso"}


@router.get('/api/index/list', summary="Vizualizar seus index")
async def list_index_router():
    response = list_index()
    return response

@router.post('/api/index/details', summary="Mostrar detalhes de um index")
async def detail_index_router(name_index: str):
    response=detail_index(name=name_index)
    return response
