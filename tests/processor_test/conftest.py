"""
Shared test fixtures for the Processor service.
Provides sample event dicts and mock helpers.
"""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def purchase_event():
    """A valid purchase_completed event."""
    return {
        "event_id": "evt-purchase-001",
        "event_type": "purchase_completed",
        "user_id": "user_001",
        "product_id": "prod_001",
        "product_name": "iPhone 15 Pro",
        "price": 129999.0,
        "quantity": 2,
        "timestamp": "2025-06-15T10:30:00Z",
        "metadata": {},
    }


@pytest.fixture
def cart_added_event():
    """A valid cart_added event."""
    return {
        "event_id": "evt-cart-001",
        "event_type": "cart_added",
        "user_id": "user_002",
        "product_id": "prod_002",
        "product_name": "MacBook Air M3",
        "price": 99999.0,
        "quantity": 1,
        "timestamp": "2025-06-15T10:31:00Z",
        "metadata": {},
    }


@pytest.fixture
def product_viewed_event():
    """A valid product_viewed event."""
    return {
        "event_id": "evt-view-001",
        "event_type": "product_viewed",
        "user_id": "user_003",
        "product_id": "prod_003",
        "product_name": "AirPods Pro 2",
        "price": 24999.0,
        "quantity": 1,
        "timestamp": "2025-06-15T10:32:00Z",
        "metadata": {},
    }


@pytest.fixture
def payment_failed_event():
    """A valid payment_failed event."""
    return {
        "event_id": "evt-fail-001",
        "event_type": "payment_failed",
        "user_id": "user_004",
        "product_id": "prod_004",
        "product_name": "PlayStation 5",
        "price": 49999.0,
        "quantity": 1,
        "timestamp": "2025-06-15T10:33:00Z",
        "metadata": {},
    }


@pytest.fixture
def mock_redis():
    """A MagicMock standing in for the Redis client."""
    return MagicMock()
