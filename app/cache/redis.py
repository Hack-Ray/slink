import json
from datetime import datetime, timedelta
from typing import Optional, Protocol, AsyncGenerator

import redis.asyncio as redis
from dotenv import load_dotenv
from app.core.config import settings


load_dotenv()

async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """Get Redis client."""
    client = redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )
    try:
        yield client
    finally:
        await client.aclose()


class CacheManagerProtocol(Protocol):
    """Protocol for cache management operations."""

    async def set_url_mapping(self, short_code: str, original_url: str, expires_at: datetime): ...

    async def get_url_mapping(self, short_code: str) -> Optional[dict]: ...

    async def increment_click_count(self, short_code: str): ...

    async def get_click_stats(self, short_code: str, days: int = 7) -> dict: ...


class RedisCacheManager:
    """Manages URL and click statistics caching using Redis."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.URL_TTL = settings.URL_TTL
        self.STATS_TTL = settings.STATS_TTL

    async def set_url_mapping(self, short_code: str, original_url: str, expires_at: datetime):
        """Stores the mapping of a short URL to its original URL in Redis."""
        key = f"url:{short_code}"
        data = {"original_url": original_url, "expires_at": expires_at.isoformat()}
        await self.redis.setex(key, self.URL_TTL, json.dumps(data))

    async def get_url_mapping(self, short_code: str) -> Optional[dict]:
        """Retrieves the original URL mapping from Redis using the short code."""
        key = f"url:{short_code}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def increment_click_count(self, short_code: str):
        """Increments the click count for a given short URL and current day."""
        today = datetime.now().strftime("%Y%m%d")
        key = f"clicks:{short_code}:{today}"
        await self.redis.incr(key)
        await self.redis.expire(key, self.STATS_TTL)

    async def get_click_stats(self, short_code: str, days: int = 7) -> dict:
        """Retrieves click statistics for a short URL over a specified number of days."""
        stats_data = {}
        for i in reversed(range(days)):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
            key = f"clicks:{short_code}:{date}"
            count = await self.redis.get(key)
            stats_data[date] = int(count) if count else 0
        return stats_data


# Default cache instance, adhering to the protocol
CacheManager: CacheManagerProtocol = RedisCacheManager
