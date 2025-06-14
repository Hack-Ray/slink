import redis
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

redis_client = redis.Redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    decode_responses=True
)

def set_url_mapping(short_code: str, original_url: str, expires_at: datetime):
    """存儲短網址映射到 Redis"""
    key = f"url:{short_code}"
    data = {
        "original_url": original_url,
        "expires_at": expires_at.isoformat()
    }
    redis_client.setex(key, 86400 * 30, json.dumps(data))  # 30天過期

def get_url_mapping(short_code: str):
    """從 Redis 獲取短網址映射"""
    key = f"url:{short_code}"
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None

def increment_click_count(short_code: str):
    """增加點擊次數"""
    today = datetime.now().strftime("%Y%m%d")
    key = f"clicks:{short_code}:{today}"
    redis_client.incr(key)
    redis_client.expire(key, 86400 * 7)  # 7天過期

def get_click_stats(short_code: str, days: int = 7):
    """獲取點擊統計"""
    stats = {}
    for i in reversed(range(days)):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        key = f"clicks:{short_code}:{date}"
        count = redis_client.get(key)
        stats[date] = int(count) if count else 0
    return stats
