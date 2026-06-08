"""
Tests for CartIQ shared CartEvent Pydantic model.
"""
import pytest
import uuid
import json
from datetime import datetime
from pydantic import ValidationError
from common.schemas.cart_event import CartEvent
from common.enums import EventType


class TestCartEventCreation:
    """Verify CartEvent model construction and defaults."""

    def test_valid_event_all_fields(self):
        event = CartEvent(
            event_id="test-id-123",
            event_type=EventType.purchase_completed,
            user_id="user_001",
            product_id="prod_001",
            product_name="iPhone 15 Pro",
            price=129999.0,
            quantity=2,
            timestamp=datetime(2025, 1, 15, 12, 0, 0),
        )
        assert event.event_id == "test-id-123"
        assert event.event_type == EventType.purchase_completed
        assert event.user_id == "user_001"
        assert event.product_id == "prod_001"
        assert event.product_name == "iPhone 15 Pro"
        assert event.price == 129999.0
        assert event.quantity == 2

    def test_auto_generated_event_id(self):
        """event_id should default to a valid UUID."""
        event = CartEvent(
            event_type=EventType.cart_added,
            user_id="user_002",
            product_id="prod_002",
            product_name="MacBook Air M3",
            price=99999.0,
        )
        # Should not raise — valid UUID format
        parsed = uuid.UUID(event.event_id)
        assert parsed.version == 4

    def test_default_quantity_is_one(self):
        event = CartEvent(
            event_type=EventType.product_viewed,
            user_id="user_003",
            product_id="prod_003",
            product_name="AirPods Pro 2",
            price=24999.0,
        )
        assert event.quantity == 1

    def test_default_timestamp_is_set(self):
        before = datetime.utcnow()
        event = CartEvent(
            event_type=EventType.product_viewed,
            user_id="user_004",
            product_id="prod_004",
            product_name="Steam Deck",
            price=39999.0,
        )
        after = datetime.utcnow()
        assert before <= event.timestamp <= after

    def test_default_metadata_is_empty_dict(self):
        event = CartEvent(
            event_type=EventType.cart_removed,
            user_id="user_005",
            product_id="prod_005",
            product_name="Kindle Paperwhite",
            price=13999.0,
        )
        assert event.metadata == {}


class TestCartEventValidation:
    """Verify CartEvent model rejects invalid data."""

    def test_invalid_event_type_raises(self):
        with pytest.raises(ValidationError):
            CartEvent(
                event_type="not_a_real_event",
                user_id="user_001",
                product_id="prod_001",
                product_name="Test",
                price=100.0,
            )

    def test_missing_user_id_raises(self):
        with pytest.raises(ValidationError):
            CartEvent(
                event_type=EventType.cart_added,
                product_id="prod_001",
                product_name="Test",
                price=100.0,
            )

    def test_missing_product_id_raises(self):
        with pytest.raises(ValidationError):
            CartEvent(
                event_type=EventType.cart_added,
                user_id="user_001",
                product_name="Test",
                price=100.0,
            )

    def test_missing_product_name_raises(self):
        with pytest.raises(ValidationError):
            CartEvent(
                event_type=EventType.cart_added,
                user_id="user_001",
                product_id="prod_001",
                price=100.0,
            )

    def test_missing_price_raises(self):
        with pytest.raises(ValidationError):
            CartEvent(
                event_type=EventType.cart_added,
                user_id="user_001",
                product_id="prod_001",
                product_name="Test",
            )


class TestCartEventSerialization:
    """Verify JSON serialization round-trip."""

    def test_json_serialization(self):
        event = CartEvent(
            event_type=EventType.purchase_completed,
            user_id="user_010",
            product_id="prod_010",
            product_name="PlayStation 5",
            price=49999.0,
            quantity=1,
        )
        data = event.model_dump()
        assert isinstance(data["event_type"], str)
        assert data["event_type"] == "purchase_completed"
        assert data["user_id"] == "user_010"

    def test_json_round_trip(self):
        event = CartEvent(
            event_type=EventType.payment_failed,
            user_id="user_011",
            product_id="prod_011",
            product_name="Xbox Series X",
            price=49999.0,
        )
        json_str = event.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["event_type"] == "payment_failed"
        assert parsed["product_name"] == "Xbox Series X"
        # timestamp should be an ISO string
        assert isinstance(parsed["timestamp"], str)
