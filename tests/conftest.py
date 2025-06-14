import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import get_db
from app.core.config import settings

# Create event loop fixture for the entire test session
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Create test database engine
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    yield engine
    await engine.dispose()

# Create test database session
@pytest_asyncio.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

# Override the get_db dependency
@pytest_asyncio.fixture
async def override_get_db(test_db: AsyncSession):
    """Override the get_db dependency."""
    async def _override_get_db():
        yield test_db
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()

# Create test client
@pytest_asyncio.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac 