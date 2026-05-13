from enum import Enum


class EventType(str, Enum):
    product_viewed = "product_viewed"
    cart_added = "cart_added"
    cart_removed = "cart_removed"
    purchase_completed = "purchase_completed"
    payment_failed = "payment_failed"


class RedisKey(str, Enum):
    revenue_total = "cartiq:revenue:total"
    top_products = "cartiq:top_products"
    active_users = "cartiq:active_users"
    events_total = "cartiq:events:total"