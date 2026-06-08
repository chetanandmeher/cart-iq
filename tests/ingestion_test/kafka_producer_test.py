"""
Tests for the Kafka producer module.
All Kafka interactions are mocked — no real broker needed.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.kafka_producer import json_serializer, publish_event, get_producer


class TestJsonSerializer:
    def test_datetime_serialization(self):
        dt = datetime(2025, 6, 15, 10, 30, 0)
        result = json_serializer(dt)
        assert result == "2025-06-15T10:30:00"

    def test_datetime_with_microseconds(self):
        dt = datetime(2025, 1, 1, 0, 0, 0, 123456)
        result = json_serializer(dt)
        assert "123456" in result

    def test_unsupported_type_raises_type_error(self):
        with pytest.raises(TypeError, match="not serializable"):
            json_serializer(set([1, 2, 3]))

    def test_unsupported_type_includes_type_name(self):
        with pytest.raises(TypeError, match="set"):
            json_serializer(set())


class TestPublishEvent:
    @patch("src.kafka_producer.get_producer")
    @pytest.mark.asyncio
    async def test_publish_success(self, mock_get_producer):
        mock_producer = MagicMock()
        mock_get_producer.return_value = mock_producer

        event = {
            "event_type": "purchase_completed",
            "user_id": "user_001",
            "product_id": "prod_001",
            "product_name": "Test Product",
            "price": 100.0,
        }

        result = await publish_event(event)
        assert result is True
        mock_producer.send.assert_called_once()
        mock_producer.flush.assert_called_once()

        # Verify topic and key
        call_kwargs = mock_producer.send.call_args
        assert call_kwargs.kwargs["topic"] == "cartiq_events"
        assert call_kwargs.kwargs["key"] == "user_001"

    @patch("src.kafka_producer.get_producer")
    @pytest.mark.asyncio
    async def test_publish_failure_returns_false(self, mock_get_producer):
        mock_producer = MagicMock()
        mock_producer.send.side_effect = Exception("Kafka connection refused")
        mock_get_producer.return_value = mock_producer

        event = {
            "event_type": "cart_added",
            "user_id": "user_002",
            "product_id": "prod_002",
            "product_name": "Test",
            "price": 50.0,
        }

        result = await publish_event(event)
        assert result is False


class TestGetProducer:
    @patch("src.kafka_producer._producer", None)
    @patch("src.kafka_producer.KafkaProducer")
    def test_creates_producer_with_correct_config(self, MockProducer):
        import src.kafka_producer
        src.kafka_producer._producer = None

        producer = get_producer()
        MockProducer.assert_called_once()
        call_kwargs = MockProducer.call_args
        assert call_kwargs.kwargs["acks"] == "all"
        assert call_kwargs.kwargs["retries"] == 3

    @patch("src.kafka_producer.KafkaProducer")
    def test_caches_producer_instance(self, MockProducer):
        import src.kafka_producer
        src.kafka_producer._producer = None

        p1 = get_producer()
        p2 = get_producer()
        # Should only create once
        MockProducer.assert_called_once()
        assert p1 is p2
