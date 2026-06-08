"""
Tests for Analytics Pydantic response schemas.
Validates structure, defaults, and data acceptance.
"""
import pytest
from src.schemas import (
    RevenueResponse,
    TopProduct,
    TopProductsResponse,
    EventCountsResponse,
    ActiveUsersResponse,
    FeedEvent,
    RevenueHistoryPoint,
    DashboardResponse,
    RedisStats,
    KafkaTopicStats,
    KafkaStats,
    InfraResponse,
    SimulatorStatus,
    SimulatorResponse,
)


class TestRevenueResponse:
    def test_valid_creation(self):
        r = RevenueResponse(total_revenue=560182.60)
        assert r.total_revenue == 560182.60

    def test_default_currency(self):
        r = RevenueResponse(total_revenue=0.0)
        assert r.currency == "INR"

    def test_custom_currency(self):
        r = RevenueResponse(total_revenue=100.0, currency="USD")
        assert r.currency == "USD"


class TestTopProduct:
    def test_valid_creation(self):
        p = TopProduct(product_name="iPhone 15 Pro", purchase_count=142)
        assert p.product_name == "iPhone 15 Pro"
        assert p.purchase_count == 142


class TestTopProductsResponse:
    def test_valid_creation(self):
        products = [
            TopProduct(product_name="iPhone", purchase_count=100),
            TopProduct(product_name="MacBook", purchase_count=50),
        ]
        r = TopProductsResponse(products=products)
        assert len(r.products) == 2

    def test_empty_products(self):
        r = TopProductsResponse(products=[])
        assert r.products == []


class TestEventCountsResponse:
    def test_valid_creation(self):
        r = EventCountsResponse(
            product_viewed=6331,
            cart_added=1120,
            cart_removed=50,
            purchase_completed=572,
            payment_failed=234,
            total=8307,
        )
        assert r.total == 8307

    def test_zero_counts(self):
        r = EventCountsResponse(
            product_viewed=0,
            cart_added=0,
            cart_removed=0,
            purchase_completed=0,
            payment_failed=0,
            total=0,
        )
        assert r.total == 0


class TestActiveUsersResponse:
    def test_valid_creation(self):
        r = ActiveUsersResponse(active_users=535)
        assert r.active_users == 535

    def test_default_window(self):
        r = ActiveUsersResponse(active_users=100)
        assert r.window == "last 5 minutes"


class TestFeedEvent:
    def test_valid_creation(self):
        f = FeedEvent(
            id="evt-001",
            type="purchase",
            title="Purchase Completed",
            subtitle="iPhone 15 Pro - ₹129999.0",
            time="Just now",
        )
        assert f.type == "purchase"
        assert f.title == "Purchase Completed"


class TestRevenueHistoryPoint:
    def test_valid_creation(self):
        p = RevenueHistoryPoint(name="10:30:00", revenue=50000.0)
        assert p.name == "10:30:00"
        assert p.revenue == 50000.0


class TestDashboardResponse:
    def test_valid_creation(self):
        d = DashboardResponse(
            revenue=RevenueResponse(total_revenue=100000.0),
            top_products=TopProductsResponse(products=[]),
            event_counts=EventCountsResponse(
                product_viewed=0, cart_added=0, cart_removed=0,
                purchase_completed=0, payment_failed=0, total=0,
            ),
            active_users=ActiveUsersResponse(active_users=0),
        )
        assert d.revenue.total_revenue == 100000.0

    def test_default_empty_lists(self):
        d = DashboardResponse(
            revenue=RevenueResponse(total_revenue=0.0),
            top_products=TopProductsResponse(products=[]),
            event_counts=EventCountsResponse(
                product_viewed=0, cart_added=0, cart_removed=0,
                purchase_completed=0, payment_failed=0, total=0,
            ),
            active_users=ActiveUsersResponse(active_users=0),
        )
        assert d.recent_events == []
        assert d.revenue_history == []


class TestRedisStats:
    def test_valid_creation(self):
        r = RedisStats(
            used_memory_human="1.5M",
            connected_clients=5,
            total_commands_processed=50000,
            keyspace_hits=4500,
            keyspace_misses=500,
            hit_ratio=90.0,
            total_keys=15,
        )
        assert r.hit_ratio == 90.0


class TestKafkaStats:
    def test_valid_creation(self):
        topic = KafkaTopicStats(topic="cartiq_events", partitions=1, message_count=0)
        k = KafkaStats(
            bootstrap_servers="kafka:9092",
            topics=[topic],
            consumer_group="cartiq-processor",
        )
        assert k.consumer_group == "cartiq-processor"
        assert len(k.topics) == 1


class TestInfraResponse:
    def test_valid_creation(self):
        redis = RedisStats(
            used_memory_human="1M", connected_clients=1,
            total_commands_processed=100, keyspace_hits=90,
            keyspace_misses=10, hit_ratio=90.0, total_keys=5,
        )
        kafka = KafkaStats(
            bootstrap_servers="kafka:9092", topics=[], consumer_group="test",
        )
        r = InfraResponse(redis=redis, kafka=kafka)
        assert r.redis.used_memory_human == "1M"


class TestSimulatorModels:
    def test_simulator_status(self):
        s = SimulatorStatus(is_running=True, events_per_second=38.2)
        assert s.is_running is True
        assert s.events_per_second == 38.2

    def test_simulator_response(self):
        r = SimulatorResponse(status="started")
        assert r.status == "started"
        assert r.message == ""

    def test_simulator_response_with_message(self):
        r = SimulatorResponse(status="error", message="Docker not available")
        assert r.message == "Docker not available"
