import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.di import get_redis
from app.services.stats_queue import StatsQueue
from app.api.url_router import router as shortener_router
from app.db.session import Base, engine
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

