from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ShortUrl
from app.db.repository import ShortUrlRepository
from app.cache.redis import CacheManagerProtocol
from app.core.config import Settings as default_settings, settings
from app.services.generators import ShortCodeGenerator, HashBasedGenerator
from app.services.url_validator import URLValidator
from app.services.stats_queue import StatsQueue


class ShortenService:
    """Handles the business logic for URL shortening and resolution."""

    def __init__(
        self,
        db_session: AsyncSession,
        generator: Optional[ShortCodeGenerator] = None,
        cache_manager: Optional[CacheManagerProtocol] = None,
        repository: Optional[ShortUrlRepository] = None,
        stats_queue: Optional[StatsQueue] = None,
        settings: Optional[settings] = None
    ):
        self.db_session = db_session
        self.repository = repository or ShortUrlRepository(db_session)
        self.generator = generator or HashBasedGenerator()
        self.cache_manager = cache_manager
        self.stats_queue = stats_queue
        self.settings = settings or default_settings() 

    async def create_short_url(self, original_url: str) -> ShortUrl:
        """Creates a new short URL or returns an existing active one."""
        # Validate URL
        async with URLValidator(self.settings) as validator:
            await validator.validate_url(str(original_url))

        existing_short_url = await self.repository.get_by_original_url(str(original_url))
        if existing_short_url:
            return existing_short_url

        short_code = await self.generator.generate(str(original_url))
        new_short_url = await self.repository.create(str(original_url), short_code)
        return new_short_url

    async def resolve_short_url(self, short_code: str) -> Optional[str]:
        """Resolves a short code to its original URL, caching if found in DB."""
        original_url = None

        # First, try to retrieve from cache
        url_data = await self.cache_manager.get_url_mapping(short_code)
        if url_data:
            original_url = url_data["original_url"]
        else:
            # If not in cache, retrieve from database
            short_url_obj = await self.repository.get_by_short_code(short_code)
            if short_url_obj:
                # Cache the mapping if found in DB
                await self.cache_manager.set_url_mapping(
                    short_code, short_url_obj.original_url, short_url_obj.expires_at
                )
                original_url = short_url_obj.original_url

        # Queue stats update if we found a valid URL
        if original_url and self.stats_queue:
            await self.stats_queue.queue_visit(short_code)

        return original_url

    async def get_url_stats(self, short_code: str) -> dict:
        """Get statistics for a short URL."""
        short_url = await self.repository.get_by_short_code(short_code)
        if not short_url:
            raise ValueError("URL not found")
        
        # Get stats from StatsQueue
        if self.stats_queue:
            stats_data = await self.stats_queue.get_stats(short_code, short_url.created_at)
            return {
                "short_code": short_code,
                "clicks": stats_data.get("clicks", {})
            }
        
        return {
            "short_code": short_code,
            "clicks": {}
        }
