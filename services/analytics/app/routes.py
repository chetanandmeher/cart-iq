import logging
import redis

from fastapi import APIRouter, HTTPException
from app.config import settings
from app.enums import RedisKey, EventType
from app.schemas import (
    RevenueResponse,
    TopProductsResponse,
    TopProduct,
    EventCountsResponse,
    ActiveUsersResponse,
    DashboardResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    decode_responses=True,
)


@router.get("/revenue", response_model=RevenueResponse)
async def get_revenue():
    total = redis_client.get(RedisKey.revenue_total)
    return RevenueResponse(total_revenue=float(total or 0))


@router.get("/top-products", response_model=TopProductsResponse)
async def get_top_products():
    raw = redis_client.zrevrange(RedisKey.top_products, 0, 9, withscores=True)
    products = [
        TopProduct(product_name=name, purchase_count=int(score))
        for name, score in raw
    ]
    return TopProductsResponse(products=products)


@router.get("/event-counts", response_model=EventCountsResponse)
async def get_event_counts():
    def get_count(event_type: EventType) -> int:
        val = redis_client.get(f"cartiq:events:{event_type.value}")
        return int(val or 0)

    total = redis_client.get(RedisKey.events_total)
    return EventCountsResponse(
        product_viewed=get_count(EventType.product_viewed),
        cart_added=get_count(EventType.cart_added),
        cart_removed=get_count(EventType.cart_removed),
        purchase_completed=get_count(EventType.purchase_completed),
        payment_failed=get_count(EventType.payment_failed),
        total=int(total or 0),
    )


@router.get("/active-users", response_model=ActiveUsersResponse)
async def get_active_users():
    count = redis_client.scard(RedisKey.active_users)
    return ActiveUsersResponse(active_users=int(count or 0))


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    revenue = await get_revenue()
    top_products = await get_top_products()
    event_counts = await get_event_counts()
    active_users = await get_active_users()

    return DashboardResponse(
        revenue=revenue,
        top_products=top_products,
        event_counts=event_counts,
        active_users=active_users,
    )


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "analytics"}