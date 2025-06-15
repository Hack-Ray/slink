from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions.exceptions import URLNotFoundError, URLValidationError, URLServiceError

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions and return standardized error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )

def register_error_handlers(app: FastAPI) -> None:
    """Register all error handlers for the application."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(URLNotFoundError, http_exception_handler)
    app.add_exception_handler(URLValidationError, http_exception_handler)
    app.add_exception_handler(URLServiceError, http_exception_handler)