import logging
import redis

from app.config import settings
from app.enums import EventType, RedisKey

logger = logging.getLogger(__name__)

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    decode_responses=True,
)


async def update_revenue(event: dict):
    """Add purchase amount to total revenue."""
    if event.get("event_type") == EventType.purchase_completed:
        amount = float(event.get("price", 0)) * int(event.get("quantity", 1))
        redis_client.incrbyfloat(RedisKey.revenue_total, amount)
        logger.info(f"Revenue updated: +{amount}")


async def update_top_products(event: dict):
    """Track top selling products by purchase count."""
    if event.get("event_type") == EventType.purchase_completed:
        product_name = event.get("product_name", "unknown")
        redis_client.zincrby(RedisKey.top_products, 1, product_name)
        logger.info(f"Top products updated: {product_name}")


async def update_event_counts(event: dict):
    """Count every event type."""
    event_type = event.get("event_type", "unknown")
    redis_client.incr(f"cartiq:events:{event_type}")
    redis_client.incr(RedisKey.events_total)


async def update_active_users(event: dict):
    """Track unique active users in last 5 minutes."""
    user_id = event.get("user_id", "unknown")
    redis_client.sadd(RedisKey.active_users, user_id)
    redis_client.expire(RedisKey.active_users, 300)