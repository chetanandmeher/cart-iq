import logging
import redis
import json
from datetime import datetime

from app.config import settings
from app.enums import EventType, RedisKey
from app.database import get_session
from app.models import Event
    
logger = logging.getLogger(__name__)

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    decode_responses=True,
)


def update_revenue(event: dict):
    """Add purchase amount to total revenue and update history."""
    if event.get("event_type") == EventType.purchase_completed:
        amount = float(event.get("price", 0)) * int(event.get("quantity", 1))
        
        # 1. Update total
        new_total = redis_client.incrbyfloat(RedisKey.revenue_total, amount)
        logger.info(f"Revenue updated: +{amount}")
        
        # 2. Update history
        now = datetime.now()
        time_str = f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}"
        
        # Optional throttle: we can just check the last element's time.
        # For simplicity, we just push it. It represents the revenue at this exact time.
        history_point = json.dumps({"name": time_str, "revenue": new_total})
        redis_client.lpush(RedisKey.revenue_history, history_point)
        redis_client.ltrim(RedisKey.revenue_history, 0, 19) # keep last 20


def update_top_products(event: dict):
    """Track top selling products by purchase count."""
    if event.get("event_type") == EventType.purchase_completed:
        product_name = event.get("product_name", "unknown")
        redis_client.zincrby(RedisKey.top_products, 1, product_name)
        logger.info(f"Top products updated: {product_name}")


def update_event_counts(event: dict):
    """Count every event type."""
    event_type = event.get("event_type", "unknown")
    redis_client.incr(f"cartiq:events:{event_type}")
    redis_client.incr(RedisKey.events_total)


def update_active_users(event: dict):
    """Track unique active users in a sliding 5-minute window."""
    user_id = event.get("user_id", "unknown")
    now = datetime.now().timestamp()
    
    # 1. Add/Update user with current timestamp
    redis_client.zadd(RedisKey.active_users, {user_id: now})
    
    # 2. Remove users who haven't been seen in the last 300 seconds
    five_mins_ago = now - 300
    redis_client.zremrangebyscore(RedisKey.active_users, "-inf", five_mins_ago)


def track_recent_events(event: dict):
    """Save recent important events for the live feed."""
    event_type = event.get("event_type", "unknown")
    
    # We only care about these 3 for the feed
    if event_type in [EventType.purchase_completed, EventType.cart_added, EventType.payment_failed]:
        # Format it exactly as the frontend expects
        
        if event_type == EventType.purchase_completed:
            t = "purchase"
            title = "Purchase Completed"
            price = float(event.get("price", 0)) * int(event.get("quantity", 1))
            subtitle = f"{event.get('product_name', 'Item')} - ₹{price}"
        elif event_type == EventType.cart_added:
            t = "cart"
            title = "Cart Added"
            subtitle = event.get("product_name", "Item")
        else:
            t = "error"
            title = "Payment Failed"
            subtitle = "Processing error"

        feed_event = {
            "id": event.get("event_id", "unknown"),
            "type": t,
            "title": title,
            "subtitle": subtitle,
            "time": "Just now" # the frontend can render this statically or based on a real timestamp
        }
        
        redis_client.lpush(RedisKey.recent_events, json.dumps(feed_event))
        redis_client.ltrim(RedisKey.recent_events, 0, 14) # keep last 15

def save_to_db(event: dict):
    """Persist raw event to PostgreSQL."""
    session = get_session()
    try:
        db_event = Event(
            event_id=event.get("event_id", str(__import__("uuid").uuid4())),
            event_type=event.get("event_type", "unknown"),
            user_id=event.get("user_id", "unknown"),
            product_id=event.get("product_id", "unknown"),
            product_name=event.get("product_name", "unknown"),
            price=float(event.get("price", 0)),
            quantity=int(event.get("quantity", 1)),
            timestamp=datetime.utcnow(),
            extra_data=event.get("metadata", {}),
        )
        session.add(db_event)
        session.commit()
        logger.info(f"Event saved to DB: {db_event.event_id}")
    except Exception as e:
        session.rollback()
        logger.error(f"DB save failed: {e}")
    finally:
        session.close()