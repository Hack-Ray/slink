import json
import os
from typing import Optional
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.di import get_db, get_redis, get_settings, get_shorten_service
from app.core.schemas import ErrorResponse
from app.services.stats_queue import StatsQueue
from app.services.shortener import ShortenService
from app.schemas.url import URLCreate, URLResponse
from app.api.shortener import router as shortener_router
from app.db.session import Base, engine
import logging
from app.core.config import settings


load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions and return standardized error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )

# Global stats queue instance
stats_queue = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global stats_queue
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    redis = await get_redis().__anext__()
    stats_queue = StatsQueue(redis=redis, settings=settings)
    await stats_queue.initialize()
    yield
    # Shutdown
    if stats_queue:
        await stats_queue.shutdown()

# Create FastAPI app
app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(shortener_router, prefix="/api")

# Register exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

@app.get("/")
async def index(request: Request):
    """Render the index page."""
    return templates.TemplateResponse("app.html", {"request": request})

@app.get("/{short_code}")
async def redirect_to_url(
    short_code: str,
    shortener: ShortenService = Depends(get_shorten_service)
):
    """Redirect to the original URL."""
    try:
        original_url = await shortener.resolve_short_url(short_code)
        if not original_url:
            raise HTTPException(status_code=404, detail="URL not found")
        return RedirectResponse(original_url)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error redirecting to URL: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error redirecting to URL"
        )

@app.get("/stats/{short_code}")
async def get_url_stats(
    short_code: str,
    request: Request,
    shorten_service = Depends(get_shorten_service)
):
    """Render the stats page for a short URL."""
    try:
        await shorten_service.get_url_stats(short_code)  # Verify the URL exists
        return templates.TemplateResponse(
            "stats.html",
            {
                "request": request,
                "short_code": short_code
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
