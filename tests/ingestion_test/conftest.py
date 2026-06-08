"""
Shared test fixtures for the Ingestion service.
Patches the Kafka producer so TestClient never connects to a real broker.
"""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture(autouse=True)
def mock_kafka_producer():
    """Prevent any real Kafka connections during tests."""
    with patch("src.kafka_producer._producer", None):
        with patch("src.kafka_producer.get_producer") as mock_get:
            mock_get.return_value = None
            yield mock_get


@pytest.fixture
def sample_event():
    """A minimal valid event payload."""
    return {
        "event_type": "purchase_completed",
        "user_id": "user_001",
        "product_id": "prod_001",
        "product_name": "iPhone 15 Pro",
        "price": 129999.0,
        "quantity": 1,
    }


@pytest.fixture
def sample_batch():
    """A batch of 3 valid events."""
    return [
        {
            "event_type": "purchase_completed",
            "user_id": "user_001",
            "product_id": "prod_001",
            "product_name": "iPhone 15 Pro",
            "price": 129999.0,
            "quantity": 1,
        },
        {
            "event_type": "cart_added",
            "user_id": "user_002",
            "product_id": "prod_002",
            "product_name": "MacBook Air M3",
            "price": 99999.0,
            "quantity": 1,
        },
        {
            "event_type": "product_viewed",
            "user_id": "user_003",
            "product_id": "prod_003",
            "product_name": "AirPods Pro 2",
            "price": 24999.0,
            "quantity": 1,
        },
    ]
