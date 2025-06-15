from fastapi.responses import RedirectResponse
from app.services.shortener import ShortenService
from app.schemas.url import URLCreate, URLResponse
from app.core.exceptions.exceptions import URLNotFoundError, URLValidationError
from app.core.config import Settings

class URLController:
    def __init__(self, shorten_service: ShortenService, settings: Settings):
        self.service = shorten_service
        self.settings = settings

    async def create_short_url(self, url_data: URLCreate) -> URLResponse:
        """Create a short URL for the given original URL."""
        try:
            result = await self.service.create_short_url(url_data.original_url)
            return URLResponse(
                short_code=result.short_code,
                original_url=result.original_url,
                created_at=result.created_at
            )
        except ValueError as e:
            raise URLValidationError(str(e))

    async def resolve_short_url(self, short_code: str) -> dict:
        """Resolves a short code to its original URL and logs click event."""
        original_url = await self.service.resolve_short_url(short_code)
        if not original_url:
            raise URLNotFoundError("Short URL not found")
        return {"original_url": original_url}

    async def redirect_to_url(self, short_code: str) -> RedirectResponse:
        """Redirect to the original URL for the given short code."""
        try:
            result = await self.service.resolve_short_url(short_code)
            return RedirectResponse(url=result)
        except ValueError as e:
            raise URLNotFoundError(str(e))

    async def get_url_stats(self, short_code: str) -> dict:
        """Get statistics for a short URL."""
        try:
            result = await self.service.get_url_stats(short_code)
            return {
                "short_code": result["short_code"],
                "clicks": result["clicks"]
            }
        except ValueError as e:
            raise URLNotFoundError(str(e)) 