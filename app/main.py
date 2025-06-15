import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.view.home import router as web_router
from app.router.api.url_router import router as api_router
from app.cache.lifespan import lifespan
from app.cache.error_handlers import register_error_handlers
from app.router.redirect_router import router as redirect_router
# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(web_router)
app.include_router(api_router, prefix="/api")
app.include_router(redirect_router)

# Register error handlers
register_error_handlers(app)

