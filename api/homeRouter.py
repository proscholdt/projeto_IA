from fastapi import APIRouter
from services.homeService import get_home_page
from fastapi.responses import FileResponse

router = APIRouter()

@router.get("/", response_class=FileResponse)
def home():
    return get_home_page()
