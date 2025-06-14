import os
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis import CacheManager
from app.core.di import get_db, get_shorten_service, get_settings
from app.core.schemas import ErrorResponse
from app.schemas.url import URLCreate, URLResponse
from app.services.shortener import ShortenService
from app.services.stats_queue import ClickEvent, StatsQueue
from app.core.config import Settings

router = APIRouter()


@router.post("/shorten", response_model=URLResponse)
async def create_short_url(
    url_data: URLCreate,
    shorten_service: ShortenService = Depends(get_shorten_service),
    settings: Settings = Depends(get_settings)
) -> URLResponse:
    """Create a short URL for the given original URL."""
    try:
        result = await shorten_service.create_short_url(url_data.original_url)
        return URLResponse(
            short_code=result.short_code,
            original_url=result.original_url,
            created_at=result.created_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get("/resolve/{short_code}")
async def resolve_short_url(
    short_code: str, shorten_service: ShortenService = Depends(get_shorten_service)
) -> dict:
    """Resolves a short code to its original URL and logs click event."""
    original_url = await shorten_service.resolve_short_url(short_code)

    if not original_url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    return {"original_url": original_url}


@router.get("/{short_code}")
async def redirect_to_url(
    short_code: str,
    request: Request,
    shorten_service: ShortenService = Depends(get_shorten_service),
    settings: Settings = Depends(get_settings)
) -> RedirectResponse:
    """Redirect to the original URL for the given short code."""
    try:
        result = await shorten_service.resolve_short_url(short_code)
        return RedirectResponse(url=result.original_url)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@router.get("/stats/{short_code}")
async def get_url_stats(
    short_code: str,
    shorten_service: ShortenService = Depends(get_shorten_service),
    settings: Settings = Depends(get_settings)
) -> dict:
    """Get statistics for a short URL."""
    try:
        result = await shorten_service.get_url_stats(short_code)
        return {
            "short_code": result["short_code"],
            "clicks": result["clicks"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        ) 