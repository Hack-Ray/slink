from typing import Callable, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.cache.redis import CacheManagerProtocol, RedisCacheManager, get_redis
from app.db.repository import ShortUrlRepository
from app.db.session import async_session, get_db
from app.services.generators import HashBasedGenerator, ShortCodeGenerator
from app.services.shortener import ShortenService
from app.services.stats_queue import StatsQueue
from app.core.config import settings, Settings
from app.controllers.url import URLController


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a SQLAlchemy session for database operations."""
    async for session in get_db():
        yield session


async def get_short_url_repository(db_session: AsyncSession = Depends(get_db_session)) -> ShortUrlRepository:
    """Dependency that provides a ShortUrlRepository instance."""
    return ShortUrlRepository(db_session)


async def get_cache_manager(redis: Redis = Depends(get_redis)) -> CacheManagerProtocol:
    """Dependency that provides a CacheManager instance (RedisCacheManager)."""
    return RedisCacheManager(redis)


def get_short_code_generator() -> ShortCodeGenerator:
    """Dependency that provides a ShortCodeGenerator instance (HashBasedGenerator)."""
    return HashBasedGenerator()


async def get_stats_queue(redis: Redis = Depends(get_redis)) -> StatsQueue:
    """Dependency that provides a StatsQueue instance."""
    return StatsQueue(redis=redis, settings=settings)


async def get_shorten_service(
    db_session: AsyncSession = Depends(get_db_session),
    generator: ShortCodeGenerator = Depends(get_short_code_generator),
    cache_manager: CacheManagerProtocol = Depends(get_cache_manager),
    repository: ShortUrlRepository = Depends(get_short_url_repository),
    stats_queue: StatsQueue = Depends(get_stats_queue)
) -> ShortenService:
    """Dependency that provides a ShortenService instance."""
    return ShortenService(
        db_session=db_session,
        generator=generator,
        cache_manager=cache_manager,
        repository=repository,
        stats_queue=stats_queue,
        settings=settings
    )


def get_db_session_factory() -> Callable[[], AsyncSession]:
    """Provides a factory function for SQLAlchemy sessions, used by background tasks."""
    return async_session


async def get_settings() -> Settings:
    """Get application settings."""
    return settings


async def get_url_controller(
    shorten_service: ShortenService = Depends(get_shorten_service),
    settings: Settings = Depends(get_settings)
) -> URLController:
    """Dependency that provides a URLController instance."""
    return URLController(shorten_service=shorten_service, settings=settings) 