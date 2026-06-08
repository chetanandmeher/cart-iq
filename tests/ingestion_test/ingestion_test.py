"""
Tests for Ingestion API routes.
Covers single event, batch, validation, and Kafka failure scenarios.
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "ingestion"}


class TestIngestSingleEvent:
    @patch("src.routes.publish_event", new_callable=AsyncMock, return_value=True)
    def test_ingest_single_event(self, mock_publish, sample_event):
        response = client.post("/api/v1/events", json=sample_event)
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert data["processed"] == 1
        assert data["failed"] == 0
        mock_publish.assert_called_once()

    @patch("src.routes.publish_event", new_callable=AsyncMock, return_value=True)
    def test_ingest_event_calls_publish_with_correct_data(self, mock_publish, sample_event):
        client.post("/api/v1/events", json=sample_event)
        call_args = mock_publish.call_args[0][0]
        assert call_args["event_type"] == "purchase_completed"
        assert call_args["user_id"] == "user_001"
        assert call_args["product_name"] == "iPhone 15 Pro"


class TestIngestBatchEvents:
    @patch("src.routes.publish_event", new_callable=AsyncMock, return_value=True)
    def test_ingest_batch(self, mock_publish, sample_batch):
        response = client.post("/api/v1/events", json=sample_batch)
        assert response.status_code == 202
        data = response.json()
        assert data["processed"] == 3
        assert data["failed"] == 0
        assert mock_publish.call_count == 3


class TestIngestValidation:
    def test_invalid_event_type(self):
        payload = {
            "event_type": "not_a_valid_type",
            "user_id": "user_001",
            "product_id": "prod_001",
            "product_name": "Test",
            "price": 100.0,
        }
        response = client.post("/api/v1/events", json=payload)
        assert response.status_code == 422

    def test_missing_user_id(self):
        payload = {
            "event_type": "purchase_completed",
            "product_id": "prod_001",
            "product_name": "Test",
            "price": 100.0,
        }
        response = client.post("/api/v1/events", json=payload)
        assert response.status_code == 422

    def test_missing_price(self):
        payload = {
            "event_type": "cart_added",
            "user_id": "user_001",
            "product_id": "prod_001",
            "product_name": "Test",
        }
        response = client.post("/api/v1/events", json=payload)
        assert response.status_code == 422

    def test_missing_product_id(self):
        payload = {
            "event_type": "cart_added",
            "user_id": "user_001",
            "product_name": "Test",
            "price": 100.0,
        }
        response = client.post("/api/v1/events", json=payload)
        assert response.status_code == 422


class TestIngestKafkaFailures:
    @patch("src.routes.publish_event", new_callable=AsyncMock, return_value=False)
    def test_all_events_fail_returns_500(self, mock_publish, sample_event):
        response = client.post("/api/v1/events", json=sample_event)
        assert response.status_code == 500
        assert "Failed to publish" in response.json()["detail"]

    @patch("src.routes.publish_event", new_callable=AsyncMock, side_effect=[True, False, True])
    def test_partial_failure_returns_202(self, mock_publish, sample_batch):
        response = client.post("/api/v1/events", json=sample_batch)
        assert response.status_code == 202
        data = response.json()
        assert data["processed"] == 3
        assert data["failed"] == 1

    @patch("src.routes.publish_event", new_callable=AsyncMock, return_value=False)
    def test_all_batch_fail_returns_500(self, mock_publish, sample_batch):
        response = client.post("/api/v1/events", json=sample_batch)
        assert response.status_code == 500
