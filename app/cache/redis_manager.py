from typing import AsyncGenerator, Optional
from redis.asyncio import Redis, ConnectionPool
from app.core.config import settings

# Create Redis connection pool
pool = ConnectionPool.from_url(
    settings.REDIS_URL,
    decode_responses=True
)

async def get_redis() -> AsyncGenerator[Redis, None]:
    """Get Redis client."""
    redis = Redis(connection_pool=pool)
    try:
        yield redis
    finally:
        await redis.close()
