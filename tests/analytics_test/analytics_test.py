"""
Tests for Analytics API routes.
All external dependencies (Redis, Kafka, Docker, PostgreSQL) are mocked.
"""
import json
import time
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
import docker
import asyncpg



class TestHealthEndpoint:
    def test_health(self, client):
        response = client.get("/api/v1/analytics/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "analytics"}


class TestRevenueEndpoint:
    def test_get_revenue(self, client, mock_redis_client):
        mock_redis_client.get.return_value = "560182.60"

        response = client.get("/api/v1/analytics/revenue")
        assert response.status_code == 200
        data = response.json()
        assert data["total_revenue"] == 560182.60
        assert data["currency"] == "INR"

    def test_get_revenue_empty(self, client, mock_redis_client):
        mock_redis_client.get.return_value = None

        response = client.get("/api/v1/analytics/revenue")
        assert response.status_code == 200
        assert response.json()["total_revenue"] == 0.0


class TestTopProductsEndpoint:
    def test_get_top_products(self, client, mock_redis_client):
        mock_redis_client.zrevrange.return_value = [
            ("iPhone 15 Pro", 142.0),
            ("MacBook Air M3", 98.0),
            ("AirPods Pro 2", 76.0),
        ]

        response = client.get("/api/v1/analytics/top-products")
        assert response.status_code == 200
        products = response.json()["products"]
        assert len(products) == 3
        assert products[0]["product_name"] == "iPhone 15 Pro"
        assert products[0]["purchase_count"] == 142

    def test_get_top_products_empty(self, client, mock_redis_client):
        mock_redis_client.zrevrange.return_value = []

        response = client.get("/api/v1/analytics/top-products")
        assert response.status_code == 200
        assert response.json()["products"] == []


class TestEventCountsEndpoint:
    def test_get_event_counts(self, client, mock_redis_client):
        mock_redis_client.get.side_effect = lambda key: {
            "cartiq:events:product_viewed": "6331",
            "cartiq:events:cart_added": "1120",
            "cartiq:events:cart_removed": "50",
            "cartiq:events:purchase_completed": "572",
            "cartiq:events:payment_failed": "234",
            "cartiq:events:total": "8307",
        }.get(key if isinstance(key, str) else key.value, "0")

        response = client.get("/api/v1/analytics/event-counts")
        assert response.status_code == 200
        data = response.json()
        assert data["product_viewed"] == 6331
        assert data["cart_added"] == 1120
        assert data["purchase_completed"] == 572
        assert data["payment_failed"] == 234
        assert data["total"] == 8307


class TestActiveUsersEndpoint:
    def test_get_active_users(self, client, mock_redis_client):
        mock_redis_client.zcard.return_value = 535

        response = client.get("/api/v1/analytics/active-users")
        assert response.status_code == 200
        data = response.json()
        assert data["active_users"] == 535
        assert data["window"] == "last 5 minutes"

    def test_active_users_cleans_expired(self, client, mock_redis_client):
        mock_redis_client.zcard.return_value = 100

        client.get("/api/v1/analytics/active-users")

        # Should have called zremrangebyscore to clean old entries
        mock_redis_client.zremrangebyscore.assert_called_once()


class TestDashboardEndpoint:
    def test_dashboard_no_period_uses_redis(self, client, mock_redis_client):
        # Set up different return values for different Redis calls
        mock_redis_client.get.side_effect = lambda key: {
            "cartiq:revenue:total": "100000.0",
            "cartiq:events:total": "500",
            "cartiq:events:product_viewed": "200",
            "cartiq:events:cart_added": "100",
            "cartiq:events:cart_removed": "10",
            "cartiq:events:purchase_completed": "150",
            "cartiq:events:payment_failed": "40",
        }.get(key if isinstance(key, str) else key.value, None)

        mock_redis_client.zrevrange.return_value = [
            ("iPhone 15 Pro", 50.0),
        ]
        mock_redis_client.zcard.return_value = 100

        # Different data for different list keys
        def lrange_side_effect(key, start, end):
            key_str = key if isinstance(key, str) else key.value
            if key_str == "cartiq:recent_events":
                return [json.dumps({
                    "id": "evt-001", "type": "purchase",
                    "title": "Purchase Completed",
                    "subtitle": "iPhone 15 Pro - ₹129999.0",
                    "time": "Just now",
                })]
            elif key_str == "cartiq:revenue:history":
                return [json.dumps({"name": "10:30:00", "revenue": 50000.0})]
            return []

        mock_redis_client.lrange.side_effect = lrange_side_effect

        response = client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 200
        data = response.json()

        assert "revenue" in data
        assert "top_products" in data
        assert "event_counts" in data
        assert "active_users" in data
        assert "recent_events" in data
        assert "revenue_history" in data

    def test_dashboard_response_structure(self, client, mock_redis_client):
        mock_redis_client.get.return_value = "0"
        mock_redis_client.zrevrange.return_value = []
        mock_redis_client.zcard.return_value = 0
        mock_redis_client.lrange.return_value = []

        response = client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 200
        data = response.json()

        assert data["revenue"]["currency"] == "INR"
        assert data["active_users"]["window"] == "last 5 minutes"
        assert isinstance(data["top_products"]["products"], list)
        assert isinstance(data["recent_events"], list)


class TestResetEndpoint:
    def test_reset_dashboard(self, client, mock_redis_client):
        response = client.post("/api/v1/analytics/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reset"
        assert "reset_at" in data

    def test_reset_deletes_redis_keys(self, client, mock_redis_client):
        client.post("/api/v1/analytics/reset")

        # Should have called delete for each aggregate key
        delete_calls = mock_redis_client.delete.call_args_list
        # Use .value to get the string value from the enum
        deleted_keys = [call[0][0].value if hasattr(call[0][0], 'value') else str(call[0][0])
                        for call in delete_calls]

        assert "cartiq:revenue:total" in deleted_keys
        assert "cartiq:top_products" in deleted_keys
        assert "cartiq:active_users" in deleted_keys
        assert "cartiq:events:total" in deleted_keys
        assert "cartiq:recent_events" in deleted_keys
        assert "cartiq:revenue:history" in deleted_keys

    def test_reset_stores_timestamp(self, client, mock_redis_client):
        client.post("/api/v1/analytics/reset")

        mock_redis_client.set.assert_called()
        set_call = mock_redis_client.set.call_args
        assert "cartiq:reset:timestamp" in str(set_call)


class TestSessionEndpoint:
    def test_get_session_with_timestamp(self, client, mock_redis_client):
        reset_time = str(time.time() - 120)  # 2 minutes ago
        mock_redis_client.get.return_value = reset_time

        response = client.get("/api/v1/analytics/session")
        assert response.status_code == 200
        data = response.json()
        assert data["reset_at"] is not None
        assert data["elapsed_seconds"] is not None
        assert data["elapsed_seconds"] >= 120

    def test_get_session_no_reset(self, client, mock_redis_client):
        mock_redis_client.get.return_value = None

        response = client.get("/api/v1/analytics/session")
        assert response.status_code == 200
        data = response.json()
        assert data["reset_at"] is None
        assert data["elapsed_seconds"] is None


class TestInfraEndpoint:
    @patch("src.routes.KafkaAdminClient")
    def test_get_infra(self, mock_kafka_admin, client, mock_redis_client):
        # Mock Redis INFO response
        mock_redis_client.info.return_value = {
            "used_memory_human": "1.5M",
            "connected_clients": 5,
            "total_commands_processed": 50000,
            "keyspace_hits": 4500,
            "keyspace_misses": 500,
            "db0": {"keys": 15},
        }

        # Mock Kafka admin
        mock_admin_instance = MagicMock()
        mock_kafka_admin.return_value = mock_admin_instance
        mock_admin_instance.list_topics.return_value = ["cartiq_events"]
        mock_admin_instance.describe_topics.return_value = [
            {"partitions": [{"id": 0}]}
        ]

        response = client.get("/api/v1/analytics/infra")
        assert response.status_code == 200
        data = response.json()

        assert data["redis"]["used_memory_human"] == "1.5M"
        assert data["redis"]["connected_clients"] == 5
        assert data["redis"]["hit_ratio"] == 90.0
        assert data["redis"]["total_keys"] == 15
        assert data["kafka"]["consumer_group"] == "cartiq-processor"


class TestSimulatorEndpoints:
    def test_simulator_status_not_found(self, client):
        """When _find_simulator_container raises, status returns unknown."""
        with patch("src.routes._find_simulator_container", side_effect=Exception("not found")):
            response = client.get("/api/v1/analytics/simulator/status")
            assert response.status_code == 200
            data = response.json()
            assert data["is_running"] is False

    def test_simulator_status_running(self, client, mock_redis_client):
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_redis_client.get.return_value = "38.2"

        with patch("src.routes._find_simulator_container", return_value=mock_container):
            response = client.get("/api/v1/analytics/simulator/status")
            assert response.status_code == 200
            data = response.json()
            assert data["is_running"] is True
            assert data["eps"] == 38.2

    def test_simulator_status_container_none(self, client):
        with patch("src.routes._find_simulator_container", return_value=None):
            response = client.get("/api/v1/analytics/simulator/status")
            assert response.status_code == 200
            data = response.json()
            assert data["is_running"] is False
            assert data["status"] == "stopped"

    def test_stop_simulator_not_found(self, client):
        with patch("src.routes._find_simulator_container", return_value=None):
            response = client.post("/api/v1/analytics/simulator/stop")
            assert response.status_code == 200
            assert response.json()["status"] == "not_found"

    def test_simulator_status_redis_error(self, client, mock_redis_client):
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_redis_client.get.side_effect = Exception("Redis connection refused")

        with patch("src.routes._find_simulator_container", return_value=mock_container):
            response = client.get("/api/v1/analytics/simulator/status")
            assert response.status_code == 200
            data = response.json()
            assert data["is_running"] is True
            assert data["eps"] == 0

    def test_stop_simulator_not_running(self, client):
        mock_container = MagicMock()
        mock_container.status = "stopped"
        with patch("src.routes._find_simulator_container", return_value=mock_container):
            response = client.post("/api/v1/analytics/simulator/stop")
            assert response.status_code == 200
            assert response.json()["status"] == "not_running"

    def test_stop_simulator_success(self, client):
        mock_container = MagicMock()
        mock_container.status = "running"
        with patch("src.routes._find_simulator_container", return_value=mock_container):
            response = client.post("/api/v1/analytics/simulator/stop")
            assert response.status_code == 200
            assert response.json()["status"] == "stopped"
            mock_container.stop.assert_called_once_with(timeout=5)

    def test_stop_simulator_exception(self, client):
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_container.stop.side_effect = Exception("Stop failed")
        with patch("src.routes._find_simulator_container", return_value=mock_container):
            response = client.post("/api/v1/analytics/simulator/stop")
            assert response.status_code == 500
            assert "Stop failed" in response.json()["detail"]

    def test_start_simulator_already_running(self, client):
        mock_container = MagicMock()
        mock_container.status = "running"
        with patch("src.routes._find_simulator_container", return_value=mock_container):
            response = client.post("/api/v1/analytics/simulator/start")
            assert response.status_code == 200
            assert response.json()["status"] == "already_running"

    def test_start_simulator_exists_stopped_success(self, client):
        mock_container = MagicMock()
        mock_container.status = "stopped"
        with patch("src.routes._find_simulator_container", return_value=mock_container):
            response = client.post("/api/v1/analytics/simulator/start")
            assert response.status_code == 200
            assert response.json()["status"] == "started"
            mock_container.start.assert_called_once()

    def test_start_simulator_exists_stopped_fails_then_recreate(self, client):
        mock_container = MagicMock()
        mock_container.status = "stopped"
        mock_container.start.side_effect = Exception("Start failed")
        
        with patch("src.routes._find_simulator_container", return_value=mock_container), \
             patch("src.routes.simulator_client") as mock_sim_client:
            
            response = client.post("/api/v1/analytics/simulator/start")
            assert response.status_code == 200
            assert response.json()["status"] == "started"
            mock_container.remove.assert_called_once_with(force=True)
            mock_sim_client.containers.run.assert_called_once()

    def test_start_simulator_not_exists_success(self, client):
        with patch("src.routes._find_simulator_container", return_value=None), \
             patch("src.routes.simulator_client") as mock_sim_client:
            
            response = client.post("/api/v1/analytics/simulator/start")
            assert response.status_code == 200
            assert response.json()["status"] == "started"
            mock_sim_client.containers.run.assert_called_once()

    def test_start_simulator_apierror_conflict_success(self, client):
        from docker.errors import APIError
        response_mock = MagicMock(status_code=409)
        api_error = APIError("Conflict name in use", response=response_mock)
        
        with patch("src.routes._find_simulator_container", return_value=None), \
             patch("src.routes.simulator_client") as mock_sim_client:
            
            mock_sim_client.containers.run.side_effect = [api_error, MagicMock()]
            
            stale_container = MagicMock()
            mock_sim_client.containers.get.return_value = stale_container
            
            response = client.post("/api/v1/analytics/simulator/start")
            assert response.status_code == 200
            assert response.json()["status"] == "started"
            assert stale_container.remove.call_count == 2
            assert mock_sim_client.containers.run.call_count == 2

    def test_start_simulator_apierror_conflict_cleanup_fails(self, client):
        from docker.errors import APIError
        response_mock = MagicMock(status_code=409)
        api_error = APIError("Conflict name in use", response=response_mock)
        
        with patch("src.routes._find_simulator_container", return_value=None), \
             patch("src.routes.simulator_client") as mock_sim_client:
            
            mock_sim_client.containers.run.side_effect = [api_error, Exception("Failed to start after cleanup")]
            
            stale_container = MagicMock()
            mock_sim_client.containers.get.return_value = stale_container
            
            response = client.post("/api/v1/analytics/simulator/start")
            assert response.status_code == 500
            assert "Failed to start after cleanup" in response.json()["detail"]

    def test_start_simulator_apierror_other(self, client):
        from docker.errors import APIError
        response_mock = MagicMock(status_code=500)
        api_error = APIError("Internal Docker Error", response=response_mock)
        
        with patch("src.routes._find_simulator_container", return_value=None), \
             patch("src.routes.simulator_client") as mock_sim_client:
            
            mock_sim_client.containers.run.side_effect = api_error
            
            response = client.post("/api/v1/analytics/simulator/start")
            assert response.status_code == 500
            assert "Docker API error" in response.json()["detail"]

    def test_start_simulator_generic_exception(self, client):
        with patch("src.routes._find_simulator_container", return_value=None), \
             patch("src.routes.simulator_client") as mock_sim_client:
            
            mock_sim_client.containers.run.side_effect = Exception("Generic Docker Error")
            
            response = client.post("/api/v1/analytics/simulator/start")
            assert response.status_code == 500
            assert "Error: Generic Docker Error" in response.json()["detail"]

    def test_find_simulator_container_not_found(self):
        from src.routes import _find_simulator_container, docker_sdk
        with patch("src.routes.simulator_client.containers.get", side_effect=docker_sdk.errors.NotFound("not found")):
            container = _find_simulator_container()
            assert container is None


class TestStartupShutdown:
    def test_startup_shutdown(self):
        from src.main import app
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            response = client.get("/api/v1/analytics/health")
            assert response.status_code == 200


class TestPostgresDashboard:
    @patch("src.routes.asyncpg.connect")
    def test_dashboard_postgres_periods(self, mock_connect, client):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        mock_conn.fetchval = AsyncMock(return_value=12500.50)
        mock_conn.fetch = AsyncMock()
        mock_conn.close = AsyncMock()
        
        mock_count_rows = [
            {"event_type": "product_viewed", "count": 120},
            {"event_type": "cart_added", "count": 45},
            {"event_type": "purchase_completed", "count": 15},
            {"event_type": "payment_failed", "count": 2},
        ]
        mock_product_rows = [
            {"product_name": "Laptop", "cnt": 10},
            {"product_name": "Phone", "cnt": 5},
        ]
        mock_history_rows = [
            {"t": datetime(2026, 6, 8, 12, 0), "rev": 5000.0},
            {"t": datetime(2026, 6, 8, 13, 0), "rev": 7500.5},
        ]

        # Test periods
        for period in ["today", "week", "month", "year", "all"]:
            mock_conn.fetch.side_effect = [
                mock_count_rows,
                mock_product_rows,
                mock_history_rows,
            ]
            response = client.get(f"/api/v1/analytics/dashboard?period={period}")
            assert response.status_code == 200
            data = response.json()
            assert data["revenue"]["total_revenue"] == 12500.50
            assert data["event_counts"]["product_viewed"] == 120
            assert data["event_counts"]["purchase_completed"] == 15
            assert data["top_products"]["products"][0]["product_name"] == "Laptop"
            assert len(data["revenue_history"]) == 2


class TestInfraKafkaError:
    @patch("src.routes.KafkaAdminClient")
    def test_get_infra_kafka_error(self, mock_kafka_admin, client, mock_redis_client):
        mock_redis_client.info.return_value = {
            "used_memory_human": "1.5M",
            "connected_clients": 5,
            "total_commands_processed": 50000,
            "keyspace_hits": 4500,
            "keyspace_misses": 500,
            "db0": {"keys": 15},
        }
        mock_kafka_admin.side_effect = Exception("Kafka connection failed")
        
        response = client.get("/api/v1/analytics/infra")
        assert response.status_code == 200
        data = response.json()
        assert data["kafka"]["topics"] == []


class TestLogStreaming:
    def test_log_streaming_invalid_service(self, client):
        response = client.get("/api/v1/analytics/logs/unknown")
        assert response.status_code == 400
        assert "Unknown service" in response.json()["detail"]

    @patch("src.routes.docker.from_env")
    def test_log_streaming_success(self, mock_docker_from_env, client):
        mock_client = MagicMock()
        mock_docker_from_env.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container
        
        mock_container.logs.return_value = [
            b"log line 1\n",
            b"log line 2\n"
        ]
        
        response = client.get("/api/v1/analytics/logs/redis")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        content = response.content
        assert b"data: log line 1" in content
        assert b"data: log line 2" in content

    @patch("src.routes.docker.from_env")
    def test_log_streaming_docker_error(self, mock_docker_from_env, client):
        mock_client = MagicMock()
        mock_docker_from_env.return_value = mock_client
        mock_client.containers.get.side_effect = Exception("Container not found")
        
        response = client.get("/api/v1/analytics/logs/redis")
        assert response.status_code == 200
        
        content = response.content
        assert b"data: ERROR: Could not connect to cart_iq-redis-1" in content


