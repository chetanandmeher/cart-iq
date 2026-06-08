from src.enums import RedisKey, EventType

def test_redis_keys():
    assert RedisKey.revenue_total == "cartiq:revenue:total"
    assert RedisKey.top_products == "cartiq:top_products"
    assert RedisKey.active_users == "cartiq:active_users"
    assert RedisKey.events_total == "cartiq:events:total"
    assert RedisKey.recent_events == "cartiq:recent_events"
    assert RedisKey.revenue_history == "cartiq:revenue:history"
    assert RedisKey.simulator_eps == "cartiq:simulator:eps"
    assert issubclass(RedisKey, str)

def test_event_types():
    assert EventType.product_viewed == "product_viewed"
    assert EventType.cart_added == "cart_added"
    assert EventType.cart_removed == "cart_removed"
    assert EventType.purchase_completed == "purchase_completed"
    assert EventType.payment_failed == "payment_failed"
    assert issubclass(EventType, str)
