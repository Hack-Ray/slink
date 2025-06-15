import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.shortener import ShortenService
from app.db.models import ShortUrl
from datetime import datetime, timedelta, UTC

@pytest.mark.asyncio
async def test_create_short_url_new(monkeypatch):
    # 準備 mock 依賴
    db_session = MagicMock()
    repository = MagicMock()
    generator = AsyncMock()
    generator.generate.return_value = "abc123"
    repository.get_by_original_url = AsyncMock(return_value=None)
    repository.create = AsyncMock(return_value=ShortUrl(
        original_url="https://test.com",
        short_code="abc123",
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=30),
        is_active=True,
        click_count=0
    ))
    service = ShortenService(
        db_session=db_session,
        generator=generator,
        repository=repository,
        cache_manager=MagicMock(),
        stats_queue=None,
        settings=MagicMock()
    )
    result = await service.create_short_url("https://test.com")
    assert result.short_code == "abc123"
    generator.generate.assert_awaited_once()
    repository.create.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_short_url_existing(monkeypatch):
    db_session = MagicMock()
    repository = MagicMock()
    generator = AsyncMock()
    existing = ShortUrl(
        original_url="https://test.com",
        short_code="abc123",
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=30),
        is_active=True,
        click_count=0
    )
    repository.get_by_original_url = AsyncMock(return_value=existing)
    service = ShortenService(
        db_session=db_session,
        generator=generator,
        repository=repository,
        cache_manager=MagicMock(),
        stats_queue=None,
        settings=MagicMock()
    )
    result = await service.create_short_url("https://test.com")
    assert result is existing
    generator.generate.assert_not_called()

@pytest.mark.asyncio
async def test_resolve_short_url_cache_hit():
    db_session = MagicMock()
    repository = MagicMock()
    cache_manager = AsyncMock()
    cache_manager.get_url_mapping = AsyncMock(return_value={"original_url": "https://test.com"})
    service = ShortenService(
        db_session=db_session,
        generator=AsyncMock(),
        repository=repository,
        cache_manager=cache_manager,
        stats_queue=None,
        settings=MagicMock()
    )
    url = await service.resolve_short_url("abc123")
    assert url == "https://test.com"
    cache_manager.get_url_mapping.assert_awaited_once()

@pytest.mark.asyncio
async def test_resolve_short_url_db_hit():
    db_session = MagicMock()
    repository = MagicMock()
    cache_manager = AsyncMock()
    repository.get_by_short_code = AsyncMock(return_value=ShortUrl(
        original_url="https://test.com",
        short_code="abc123",
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=30),
        is_active=True,
        click_count=0
    ))
    cache_manager.get_url_mapping = AsyncMock(return_value=None)
    cache_manager.set_url_mapping = AsyncMock()
    service = ShortenService(
        db_session=db_session,
        generator=AsyncMock(),
        repository=repository,
        cache_manager=cache_manager,
        stats_queue=None,
        settings=MagicMock()
    )
    url = await service.resolve_short_url("abc123")
    assert url == "https://test.com"
    cache_manager.set_url_mapping.assert_awaited_once()

@pytest.mark.asyncio
async def test_resolve_short_url_not_found():
    db_session = MagicMock()
    repository = MagicMock()
    cache_manager = AsyncMock()
    repository.get_by_short_code = AsyncMock(return_value=None)
    cache_manager.get_url_mapping = AsyncMock(return_value=None)
    service = ShortenService(
        db_session=db_session,
        generator=AsyncMock(),
        repository=repository,
        cache_manager=cache_manager,
        stats_queue=None,
        settings=MagicMock()
    )
    url = await service.resolve_short_url("notfound")
    assert url is None

@pytest.mark.asyncio
async def test_get_url_stats_success():
    db_session = MagicMock()
    repository = MagicMock()
    stats_queue = AsyncMock()
    repository.get_by_short_code = AsyncMock(return_value=ShortUrl(
        original_url="https://test.com",
        short_code="abc123",
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=30),
        is_active=True,
        click_count=0
    ))
    stats_queue.get_stats = AsyncMock(return_value={"clicks": {"20240101": 5}})
    service = ShortenService(
        db_session=db_session,
        generator=AsyncMock(),
        repository=repository,
        cache_manager=AsyncMock(),
        stats_queue=stats_queue,
        settings=MagicMock()
    )
    stats = await service.get_url_stats("abc123")
    assert stats["clicks"] == {"20240101": 5}

@pytest.mark.asyncio
async def test_get_url_stats_not_found():
    db_session = MagicMock()
    repository = MagicMock()
    repository.get_by_short_code = AsyncMock(return_value=None)
    service = ShortenService(
        db_session=db_session,
        generator=AsyncMock(),
        repository=repository,
        cache_manager=AsyncMock(),
        stats_queue=None,
        settings=MagicMock()
    )
    with pytest.raises(ValueError):
        await service.get_url_stats("notfound") 