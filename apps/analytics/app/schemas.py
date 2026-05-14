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


class FeedEvent(BaseModel):
    id: str
    type: str
    title: str
    subtitle: str
    time: str


class RevenueHistoryPoint(BaseModel):
    name: str
    revenue: float


class DashboardResponse(BaseModel):
    revenue: RevenueResponse
    top_products: TopProductsResponse
    event_counts: EventCountsResponse
    active_users: ActiveUsersResponse
    recent_events: List[FeedEvent] = []
    revenue_history: List[RevenueHistoryPoint] = []

class RedisStats(BaseModel):
    used_memory_human: str
    connected_clients: int
    total_commands_processed: int
    keyspace_hits: int
    keyspace_misses: int
    hit_ratio: float
    total_keys: int


class KafkaTopicStats(BaseModel):
    topic: str
    partitions: int
    message_count: int


class KafkaStats(BaseModel):
    bootstrap_servers: str
    topics: List[KafkaTopicStats]
    consumer_group: str


class InfraResponse(BaseModel):
    redis: RedisStats
    kafka: KafkaStats

class SimulatorStatus(BaseModel):
    is_running: bool
    events_per_second: float

class SimulatorResponse(BaseModel):
    status: str
    message: str = ""