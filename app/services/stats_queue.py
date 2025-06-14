import threading
import time
import asyncio
from queue import Queue
from datetime import datetime, timedelta
from typing import Callable, List, Optional
import json
import logging
import backoff
from redis.asyncio import Redis
from app.core.config import Settings

from sqlalchemy.orm import Session

from app.db.models import ShortUrl
from app.db.repository import ShortUrlRepository

logger = logging.getLogger(__name__)

class ClickEvent:
    """Represents a single click event for a short URL."""

    def __init__(self, short_code: str):
        self.short_code = short_code
        self.timestamp = datetime.now()


class StatsQueue:
    """Manages a queue for click events and processes them in batches asynchronously."""

    def __init__(
        self,
        redis: Redis,
        settings: Settings,
        queue_name: str = "url_stats"
    ):
        self.redis = redis
        self.settings = settings
        self.queue_name = queue_name
        self._processing_task = None
        self._stop_event = asyncio.Event()

    async def initialize(self) -> None:
        """Initialize the stats queue and start the processing task."""
        self._processing_task = asyncio.create_task(self._process_visits_loop())
        logger.info("Stats queue initialized and processing task started")

    async def shutdown(self) -> None:
        """Shutdown the stats queue and stop the processing task."""
        if self._processing_task:
            self._stop_event.set()
            await self._processing_task
            self._processing_task = None
        logger.info("Stats queue shutdown complete")

    async def _process_visits_loop(self) -> None:
        """Background task to process visits continuously."""
        while not self._stop_event.is_set():
            try:
                await self.process_visits()
                await asyncio.sleep(1)  # Wait before next batch
            except Exception as e:
                logger.error(f"Error in visit processing loop: {str(e)}")
                await asyncio.sleep(5)  # Wait longer on error

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=30
    )
    async def queue_visit(self, short_code: str) -> None:
        """Queue a URL visit for statistics processing."""
        try:
            visit_data = {
                "short_code": short_code,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.redis.lpush(self.queue_name, json.dumps(visit_data))
            logger.info(f"Queued visit for short_code: {short_code}")
            
            # Process visits immediately to ensure real-time updates
            await self.process_visits()
        except Exception as e:
            logger.error(f"Error queueing visit for {short_code}: {str(e)}")
            raise

    async def process_visits(self, batch_size: int = 100) -> None:
        """Process queued visits in batches."""
        try:
            # Get batch of visits
            visits = await self.redis.lrange(self.queue_name, 0, batch_size - 1)
            if not visits:
                return

            # Process each visit
            for visit_json in visits:
                try:
                    visit_data = json.loads(visit_json)
                    await self._process_single_visit(visit_data)
                    # Remove processed visit from queue
                    await self.redis.lrem(self.queue_name, 1, visit_json)
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding visit data: {str(e)}")
                    # Remove invalid data from queue
                    await self.redis.lrem(self.queue_name, 1, visit_json)
                except Exception as e:
                    logger.error(f"Error processing visit: {str(e)}")
                    # Mark visit as failed
                    visit_data["error"] = str(e)
                    visit_data["processed"] = False
                    await self.redis.lrem(self.queue_name, 1, visit_json)
                    await self.redis.lpush(f"{self.queue_name}:failed", json.dumps(visit_data))

        except Exception as e:
            logger.error(f"Error in process_visits: {str(e)}")
            raise

    async def _process_single_visit(self, visit_data: dict) -> None:
        """Process a single visit record."""
        try:
            short_code = visit_data["short_code"]
            timestamp = datetime.fromisoformat(visit_data["timestamp"])
            date_key = timestamp.strftime("%Y%m%d")  # Format as YYYYMMDD for consistency

            # Use Redis transaction to ensure atomic updates
            async with self.redis.pipeline(transaction=True) as pipe:
                # Update daily stats
                await pipe.hincrby(
                    f"url:stats:{short_code}:daily",
                    date_key,
                    1
                )

                # Execute all commands atomically
                await pipe.execute()

            logger.info(f"Processed visit for {short_code} on {date_key}")
        except Exception as e:
            logger.error(f"Error processing visit data: {str(e)}")
            raise

    async def get_stats(self, short_code: str, created_at: datetime) -> dict:
        """Get statistics for a URL, including daily clicks for the last 7 days."""
        try:
            raw_daily_stats = await self.redis.hgetall(f"url:stats:{short_code}:daily")
            
            # Calculate date range for last 7 days
            today = datetime.now().date()
            start_date = today - timedelta(days=6)  # 7 days including today
            
            # Generate daily clicks for the last 7 days
            daily_clicks = {}
            current_date = start_date
            
            while current_date <= today:
                date_str = current_date.strftime("%Y%m%d")  # Format as YYYYMMDD
                daily_clicks[date_str] = int(raw_daily_stats.get(date_str, 0))
                current_date += timedelta(days=1)

            return {
                "short_code": short_code,
                "clicks": daily_clicks
            }
        except Exception as e:
            logger.error(f"Error getting stats for {short_code}: {str(e)}")
            return {
                "short_code": short_code,
                "clicks": {}
            } 