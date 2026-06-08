"""
Shared test fixtures for the Analytics service.
Patches Docker and Redis BEFORE the app module is imported.
"""
import sys
import pytest
import json
from unittest.mock import patch, MagicMock

# --- Pre-import Docker mock ---
# docker.from_env() is called at module level in src/routes.py (line 33).
# We must patch it before pytest imports the test modules which import src.main.
_mock_docker_client = MagicMock()

# Patch docker module before routes.py can import it
import docker as _docker_module
_original_from_env = _docker_module.from_env
_docker_module.from_env = lambda **kwargs: _mock_docker_client


@pytest.fixture(autouse=True)
def mock_docker():
    """Provide the pre-patched mock Docker client to tests."""
    _mock_docker_client.reset_mock()
    yield _mock_docker_client


@pytest.fixture
def mock_redis_client():
    """Provide a mock Redis client and patch it into routes."""
    mock = MagicMock()
    with patch("src.routes.redis_client", mock):
        yield mock


@pytest.fixture
def client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from src.main import app
    return TestClient(app)


@pytest.fixture
def dashboard_redis_data(mock_redis_client):
    """Set up mock Redis to return realistic dashboard data."""
    mock_redis_client.get.side_effect = lambda key: {
        "cartiq:revenue:total": "560182.60",
        "cartiq:events:total": "8257",
        "cartiq:events:product_viewed": "6331",
        "cartiq:events:cart_added": "1120",
        "cartiq:events:cart_removed": "0",
        "cartiq:events:purchase_completed": "572",
        "cartiq:events:payment_failed": "234",
    }.get(key if isinstance(key, str) else key.value, None)

    mock_redis_client.zrevrange.return_value = [
        ("iPhone 15 Pro", 142.0),
        ("MacBook Air M3", 98.0),
    ]

    mock_redis_client.zcard.return_value = 535

    mock_redis_client.lrange.return_value = [
        json.dumps({
            "id": "evt-001",
            "type": "purchase",
            "title": "Purchase Completed",
            "subtitle": "iPhone 15 Pro - ₹129999.0",
            "time": "Just now",
        })
    ]

    return mock_redis_client
