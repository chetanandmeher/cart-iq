from pydantic import BaseModel
from typing import List


class RevenueResponse(BaseModel):
    total_revenue: float
    currency: str = "INR"


class TopProduct(BaseModel):
    product_name: str
    purchase_count: int


class TopProductsResponse(BaseModel):
    products: List[TopProduct]


class EventCountsResponse(BaseModel):
    product_viewed: int
    cart_added: int
    cart_removed: int
    purchase_completed: int
    payment_failed: int
    total: int


class ActiveUsersResponse(BaseModel):
    active_users: int
    window: str = "last 5 minutes"


class DashboardResponse(BaseModel):
    revenue: RevenueResponse
    top_products: TopProductsResponse
    event_counts: EventCountsResponse
    active_users: ActiveUsersResponse