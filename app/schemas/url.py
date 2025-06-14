from datetime import datetime
from pydantic import BaseModel, HttpUrl
from pydantic import ConfigDict

class URLCreate(BaseModel):
    """Schema for creating a new short URL."""
    original_url: HttpUrl

class URLResponse(BaseModel):
    """Schema for URL response."""
    short_code: str
    original_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)