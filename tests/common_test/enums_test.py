"""
Tests for CartIQ shared enums — EventType and RedisKey.
"""
from common.enums import EventType, RedisKey


class TestEventType:
    """Verify EventType enum members and behavior."""

    def test_has_exactly_five_members(self):
        assert len(EventType) == 5

    def test_member_values(self):
        assert EventType.product_viewed == "product_viewed"
        assert EventType.cart_added == "cart_added"
        assert EventType.cart_removed == "cart_removed"
        assert EventType.purchase_completed == "purchase_completed"
        assert EventType.payment_failed == "payment_failed"

    def test_is_str_subclass(self):
        """EventType members should be usable as plain strings."""
        for member in EventType:
            assert isinstance(member, str)
            assert isinstance(member.value, str)

    def test_string_comparison(self):
        """Enum values should compare equal to their string equivalents."""
        assert EventType.purchase_completed == "purchase_completed"
        assert "cart_added" == EventType.cart_added

    def test_lookup_by_value(self):
        assert EventType("product_viewed") is EventType.product_viewed

    def test_invalid_value_raises(self):
        import pytest
        with pytest.raises(ValueError):
            EventType("invalid_event")


class TestRedisKey:
    """Verify RedisKey enum members and prefix convention."""

    def test_has_exactly_six_members(self):
        assert len(RedisKey) == 6

    def test_member_values(self):
        assert RedisKey.revenue_total == "cartiq:revenue:total"
        assert RedisKey.top_products == "cartiq:top_products"
        assert RedisKey.active_users == "cartiq:active_users"
        assert RedisKey.events_total == "cartiq:events:total"
        assert RedisKey.recent_events == "cartiq:recent_events"
        assert RedisKey.revenue_history == "cartiq:revenue:history"

    def test_all_keys_have_cartiq_prefix(self):
        for member in RedisKey:
            assert member.value.startswith("cartiq:"), (
                f"{member.name} does not start with 'cartiq:'"
            )

    def test_is_str_subclass(self):
        for member in RedisKey:
            assert isinstance(member, str)
