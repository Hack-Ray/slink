from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.di import get_redis
from app.services.stats_queue import StatsQueue
from app.db.session import Base, engine
from app.core.config import settings

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