from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str
    TEST_DATABASE_URL: str
    DB_ECHO: bool

    # Redis settings
    REDIS_URL: str
    URL_TTL: int
    STATS_TTL: int

    # Google Safe Browsing API
    GOOGLE_SAFE_BROWSING_API_KEY: Optional[str] = None

    # Application settings
    APP_NAME: str
    DEBUG: bool
    SECRET_KEY: str
    BASE_URL: str

    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="allow")

settings = Settings() 