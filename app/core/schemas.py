from pydantic import BaseModel
from typing import Optional


class ErrorResponse(BaseModel):
    """Standard error response format for the API."""

    detail: str
    code: Optional[str] = None
    status_code: int 