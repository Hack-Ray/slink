from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func
from .session import Base

class ShortUrl(Base):
    """Represents a shortened URL entry in the database."""

    __tablename__ = "short_urls"

    id = Column(Integer, primary_key=True, index=True, doc="Unique identifier for the short URL")
    original_url = Column(String, nullable=False, doc="The original, long URL")
    short_code = Column(String, unique=True, index=True, nullable=False, doc="The generated short code")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), doc="Timestamp of creation")
    expires_at = Column(DateTime(timezone=True), nullable=False, doc="Timestamp when the short URL expires")
    is_active = Column(Boolean, default=True, doc="Indicates if the short URL is active")
    click_count = Column(Integer, default=0, doc="Number of times the short URL has been clicked")
