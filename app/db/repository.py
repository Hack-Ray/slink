from datetime import datetime, timedelta, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from .models import ShortUrl


class ShortUrlRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_original_url(self, original_url: str) -> Optional[ShortUrl]:
        """Get an active short URL by its original URL."""
        now = datetime.now(UTC)
        query = select(ShortUrl).where(
            ShortUrl.original_url == original_url,
            ShortUrl.expires_at > now
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_short_code(self, short_code: str) -> Optional[ShortUrl]:
        """Get an active short URL by its short code."""
        now = datetime.now(UTC)
        query = select(ShortUrl).where(
            ShortUrl.short_code == short_code,
            ShortUrl.expires_at > now
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, original_url: str, short_code: str, expires_days: int = 30) -> ShortUrl:
        """Create a new short URL entry in the database."""
        now = datetime.now(UTC)
        short_url = ShortUrl(
            original_url=original_url,
            short_code=short_code,
            expires_at=now + timedelta(days=expires_days)
        )
        self.db_session.add(short_url)
        await self.db_session.commit()
        await self.db_session.refresh(short_url)
        return short_url

    async def increment_click_count(self, short_code: str, count: int = 1):
        """Increment the click count for a short URL."""
        query = select(ShortUrl).where(ShortUrl.short_code == short_code)
        result = await self.db_session.execute(query)
        short_url_obj = result.scalar_one_or_none()
        if short_url_obj:
            short_url_obj.click_count += count
            await self.db_session.commit() 