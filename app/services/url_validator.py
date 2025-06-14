from typing import Optional
from urllib.parse import urlparse
import aiohttp
from fastapi import HTTPException
from app.core.config import Settings


class URLValidator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
            self._session = None

    def validate_url_format(self, url: str) -> None:
        """Validate URL format."""
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise ValueError("Invalid URL format")
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid URL format: {str(e)}"
            )

    async def check_safe_browsing(self, url: str) -> None:
        """Check URL against Google Safe Browsing API."""
        if not self.settings.GOOGLE_SAFE_BROWSING_API_KEY:
            return

        if not self._session:
            raise RuntimeError("Session not initialized. Use async context manager.")

        payload = {
            "client": {
                "clientId": "slink",
                "clientVersion": "1.0.0"
            },
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": str(url)}]
            }
        }

        try:
            async with self._session.post(
                f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={self.settings.GOOGLE_SAFE_BROWSING_API_KEY}",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:  # If there's a match, the URL is unsafe
                        raise HTTPException(
                            status_code=400,
                            detail="URL is not safe according to Google Safe Browsing"
                        )
        except aiohttp.ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error checking URL safety: {str(e)}"
            )

    async def validate_url(self, url: str) -> None:
        """Validate URL format and safety."""
        self.validate_url_format(url)
        await self.check_safe_browsing(url) 