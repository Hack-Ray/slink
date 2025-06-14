from hashids import Hashids
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..db.models import ShortUrl
from ..cache.redis import set_url_mapping
from sqlalchemy.sql import func

def generate_short_code(url_id: int) -> str:
    """生成短網址代碼"""
    salt = os.getenv("SECRET_KEY", "your-secret-key-here")
    hashids = Hashids(salt=salt, min_length=6)
    return hashids.encode(url_id)

def create_short_url(db: Session, original_url: str) -> ShortUrl:
    """創建短網址記錄，若已存在且未過期則直接回傳"""
    now = datetime.now()
    existing = db.query(ShortUrl).filter(
        ShortUrl.original_url == original_url,
        ShortUrl.expires_at > now
    ).first()
    if existing:
        return existing

    temp_id = db.query(func.max(ShortUrl.id)).scalar() or 0
    temp_id += 1
    short_code = generate_short_code(temp_id)
    short_url = ShortUrl(
        original_url=original_url,
        short_code=short_code,
        expires_at=now + timedelta(days=30)
    )
    db.add(short_url)
    db.commit()
    db.refresh(short_url)
    set_url_mapping(short_code, original_url, short_url.expires_at)
    return short_url
