import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_short_url_success(async_client: AsyncClient):
    resp = await async_client.post("/api/shorten", json={"original_url": "https://example.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert "short_code" in data
    assert data["original_url"].rstrip('/') == "https://example.com"

@pytest.mark.asyncio
async def test_create_short_url_invalid(async_client: AsyncClient):
    resp = await async_client.post("/api/shorten", json={"original_url": "not_a_url"})
    assert resp.status_code in [422, 400]

@pytest.mark.asyncio
async def test_resolve_short_url_success(async_client: AsyncClient):
    # 先產生短網址
    resp = await async_client.post("/api/shorten", json={"original_url": "https://github.com"})
    short_code = resp.json()["short_code"]
    # 測試 resolve
    resp2 = await async_client.get(f"/api/resolve/{short_code}")
    assert resp2.status_code == 200
    assert resp2.json()["original_url"].rstrip('/') == "https://github.com"

@pytest.mark.asyncio
async def test_resolve_short_url_not_found(async_client: AsyncClient):
    resp = await async_client.get("/api/resolve/doesnotexist")
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_stats_clicks_accumulate(async_client: AsyncClient):
    # 先產生短網址
    resp = await async_client.post("/api/shorten", json={"original_url": "https://pytest.org"})
    short_code = resp.json()["short_code"]
    # 模擬多次訪問
    for _ in range(3):
        await async_client.get(f"/{short_code}")
    # 查詢統計
    resp2 = await async_client.get(f"/api/stats/{short_code}")
    assert resp2.status_code == 200
    data = resp2.json()
    assert "clicks" in data
    assert sum(data["clicks"].values()) >= 3  # 點擊數應累加 