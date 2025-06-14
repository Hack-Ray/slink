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

class RedisCache:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        return await self.redis.get(key)

    async def set(self, key: str, value: str, expire: int = 3600) -> None:
        """Set value in cache."""
        await self.redis.set(key, value, ex=expire)

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return bool(await self.redis.exists(key)) 