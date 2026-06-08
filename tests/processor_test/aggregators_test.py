"""
Tests for all 6 Redis aggregators and the PostgreSQL save function.
Uses unittest.mock.patch to mock the Redis client and DB session.
"""
import json
import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime


class TestUpdateRevenue:
    @patch("src.aggregators.redis_client")
    def test_purchase_updates_revenue(self, mock_redis, purchase_event):
        mock_redis.incrbyfloat.return_value = 259998.0
        from src.aggregators import update_revenue

        update_revenue(purchase_event)

        expected_amount = 129999.0 * 2  # price * quantity
        mock_redis.incrbyfloat.assert_called_once_with(
            "cartiq:revenue:total", expected_amount
        )

    @patch("src.aggregators.redis_client")
    def test_purchase_pushes_history(self, mock_redis, purchase_event):
        mock_redis.incrbyfloat.return_value = 259998.0
        from src.aggregators import update_revenue

        update_revenue(purchase_event)

        mock_redis.lpush.assert_called_once()
        mock_redis.ltrim.assert_called_once_with("cartiq:revenue:history", 0, 19)

    @patch("src.aggregators.redis_client")
    def test_non_purchase_does_not_update_revenue(self, mock_redis, cart_added_event):
        from src.aggregators import update_revenue

        update_revenue(cart_added_event)

        mock_redis.incrbyfloat.assert_not_called()
        mock_redis.lpush.assert_not_called()

    @patch("src.aggregators.redis_client")
    def test_revenue_history_contains_valid_json(self, mock_redis, purchase_event):
        mock_redis.incrbyfloat.return_value = 100000.0
        from src.aggregators import update_revenue

        update_revenue(purchase_event)

        history_arg = mock_redis.lpush.call_args[0][1]
        parsed = json.loads(history_arg)
        assert "name" in parsed
        assert "revenue" in parsed
        assert parsed["revenue"] == 100000.0


class TestUpdateTopProducts:
    @patch("src.aggregators.redis_client")
    def test_purchase_increments_product_score(self, mock_redis, purchase_event):
        from src.aggregators import update_top_products

        update_top_products(purchase_event)

        mock_redis.zincrby.assert_called_once_with(
            "cartiq:top_products", 1, "iPhone 15 Pro"
        )

    @patch("src.aggregators.redis_client")
    def test_non_purchase_does_not_update(self, mock_redis, product_viewed_event):
        from src.aggregators import update_top_products

        update_top_products(product_viewed_event)

        mock_redis.zincrby.assert_not_called()


class TestUpdateEventCounts:
    @patch("src.aggregators.redis_client")
    def test_increments_type_specific_key(self, mock_redis, purchase_event):
        from src.aggregators import update_event_counts

        update_event_counts(purchase_event)

        mock_redis.incr.assert_any_call("cartiq:events:purchase_completed")

    @patch("src.aggregators.redis_client")
    def test_increments_total_key(self, mock_redis, purchase_event):
        from src.aggregators import update_event_counts

        update_event_counts(purchase_event)

        mock_redis.incr.assert_any_call("cartiq:events:total")

    @patch("src.aggregators.redis_client")
    def test_counts_all_event_types(self, mock_redis):
        from src.aggregators import update_event_counts

        for event_type in ["product_viewed", "cart_added", "cart_removed",
                           "purchase_completed", "payment_failed"]:
            mock_redis.reset_mock()
            update_event_counts({"event_type": event_type})
            mock_redis.incr.assert_any_call(f"cartiq:events:{event_type}")


class TestUpdateActiveUsers:
    @patch("src.aggregators.redis_client")
    def test_adds_user_to_sorted_set(self, mock_redis, purchase_event):
        from src.aggregators import update_active_users

        update_active_users(purchase_event)

        mock_redis.zadd.assert_called_once()
        call_args = mock_redis.zadd.call_args
        assert "cartiq:active_users" in call_args[0]
        # The second arg is a dict {user_id: timestamp}
        user_scores = call_args[0][1]
        assert "user_001" in user_scores

    @patch("src.aggregators.redis_client")
    def test_removes_expired_users(self, mock_redis, purchase_event):
        from src.aggregators import update_active_users

        update_active_users(purchase_event)

        mock_redis.zremrangebyscore.assert_called_once()
        call_args = mock_redis.zremrangebyscore.call_args[0]
        assert call_args[0] == "cartiq:active_users"
        assert call_args[1] == "-inf"


class TestTrackRecentEvents:
    @patch("src.aggregators.redis_client")
    def test_purchase_creates_feed_event(self, mock_redis, purchase_event):
        from src.aggregators import track_recent_events

        track_recent_events(purchase_event)

        mock_redis.lpush.assert_called_once()
        feed_json = mock_redis.lpush.call_args[0][1]
        feed = json.loads(feed_json)
        assert feed["type"] == "purchase"
        assert feed["title"] == "Purchase Completed"
        assert "iPhone 15 Pro" in feed["subtitle"]
        assert "₹" in feed["subtitle"]

    @patch("src.aggregators.redis_client")
    def test_cart_added_creates_feed_event(self, mock_redis, cart_added_event):
        from src.aggregators import track_recent_events

        track_recent_events(cart_added_event)

        feed_json = mock_redis.lpush.call_args[0][1]
        feed = json.loads(feed_json)
        assert feed["type"] == "cart"
        assert feed["title"] == "Cart Added"
        assert feed["subtitle"] == "MacBook Air M3"

    @patch("src.aggregators.redis_client")
    def test_payment_failed_creates_feed_event(self, mock_redis, payment_failed_event):
        from src.aggregators import track_recent_events

        track_recent_events(payment_failed_event)

        feed_json = mock_redis.lpush.call_args[0][1]
        feed = json.loads(feed_json)
        assert feed["type"] == "error"
        assert feed["title"] == "Payment Failed"

    @patch("src.aggregators.redis_client")
    def test_product_viewed_does_not_push(self, mock_redis, product_viewed_event):
        from src.aggregators import track_recent_events

        track_recent_events(product_viewed_event)

        mock_redis.lpush.assert_not_called()

    @patch("src.aggregators.redis_client")
    def test_recent_events_trimmed_to_15(self, mock_redis, purchase_event):
        from src.aggregators import track_recent_events

        track_recent_events(purchase_event)

        mock_redis.ltrim.assert_called_once_with("cartiq:recent_events", 0, 14)


class TestSaveToDb:
    @patch("src.aggregators.get_session")
    def test_saves_event_to_database(self, mock_get_session, purchase_event):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        from src.aggregators import save_to_db

        save_to_db(purchase_event)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

        # Verify the Event object fields
        saved_event = mock_session.add.call_args[0][0]
        assert saved_event.event_id == "evt-purchase-001"
        assert saved_event.event_type == "purchase_completed"
        assert saved_event.user_id == "user_001"
        assert saved_event.product_name == "iPhone 15 Pro"
        assert saved_event.price == 129999.0
        assert saved_event.quantity == 2

    @patch("src.aggregators.get_session")
    def test_rollback_on_failure(self, mock_get_session, purchase_event):
        mock_session = MagicMock()
        mock_session.commit.side_effect = Exception("DB connection lost")
        mock_get_session.return_value = mock_session

        from src.aggregators import save_to_db

        # Should not raise — error is caught internally
        save_to_db(purchase_event)

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("src.aggregators.get_session")
    def test_session_always_closed(self, mock_get_session, purchase_event):
        mock_session = MagicMock()
        mock_session.commit.side_effect = Exception("Error")
        mock_get_session.return_value = mock_session

        from src.aggregators import save_to_db

        save_to_db(purchase_event)

        # close() is called even on failure (finally block)
        mock_session.close.assert_called_once()
