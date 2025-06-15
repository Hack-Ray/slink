from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from app.controllers.url import URLController
from app.core.di import get_url_controller

router = APIRouter()

@router.get("/{short_code}")
async def redirect_to_url(
    short_code: str,
    controller: URLController = Depends(get_url_controller)
) -> RedirectResponse:
    """Redirect to the original URL for the given short code."""
    return await controller.redirect_to_url(short_code)