from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def index(request: Request):
    """Render the index page."""
    return templates.TemplateResponse("app.html", {"request": request}) 