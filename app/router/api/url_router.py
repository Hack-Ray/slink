from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from app.core.di import get_url_controller
from app.schemas.url import URLCreate, URLResponse
from app.controllers.url import URLController

router = APIRouter()


@router.post("/shorten", response_model=URLResponse)
async def create_short_url(
    url_data: URLCreate,
    controller: URLController = Depends(get_url_controller)
) -> URLResponse:
    """Create a short URL for the given original URL."""
    return await controller.create_short_url(url_data)


@router.get("/resolve/{short_code}")
async def resolve_short_url(
    short_code: str,
    controller: URLController = Depends(get_url_controller)
) -> dict:
    """Resolves a short code to its original URL and logs click event."""
    return await controller.resolve_short_url(short_code)


@router.get("/stats/{short_code}")
async def get_url_stats(
    short_code: str,
    controller: URLController = Depends(get_url_controller)
) -> dict:
    """Get statistics for a short URL."""
    return await controller.get_url_stats(short_code) 