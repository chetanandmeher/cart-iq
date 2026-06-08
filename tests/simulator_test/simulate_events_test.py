import threading
import time
import pytest
import json
from unittest.mock import patch, MagicMock
import src.simulate_events as sim

def test_products_and_users_initialized():
    assert len(sim.PRODUCTS) == 100
    assert len(sim.USER_IDS) == 1000
    assert sim.PRODUCTS[0]["id"] is not None
    assert sim.PRODUCTS[0]["name"] is not None
    assert isinstance(sim.PRODUCTS[0]["price"], int)

def test_make_event():
    product = {"id": "prod-123", "name": "Test Product", "price": 999}
    user_id = "user-456"
    event = sim.make_event("cart_added", product, user_id)
    
    assert event["event_type"] == "cart_added"
    assert event["user_id"] == "user-456"
    assert event["product_id"] == "prod-123"
    assert event["product_name"] == "Test Product"
    assert event["price"] == 999
    assert 1 <= event["quantity"] <= 3
    assert event["event_id"] is not None
    assert event["session_id"] is not None
    assert event["timestamp"] is not None

def test_batch_sender_success():
    with patch("src.simulate_events.requests.post") as mock_post, \
         patch("src.simulate_events.redis_client") as mock_redis:
        
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_post.return_value = mock_response
        
        # Reset queue
        while not sim.event_queue.empty():
            try:
                sim.event_queue.get_nowait()
            except:
                pass
                
        sim.total_sent = 90  # set to 90 so sending 10 will trigger Redis write
        
        # Start batch sender in a daemon thread
        t = threading.Thread(target=sim.batch_sender, daemon=True)
        t.start()
        
        # Put 10 events (BATCH_SIZE) in queue
        product = sim.PRODUCTS[0]
        for _ in range(10):
            sim.event_queue.put(sim.make_event("product_viewed", product, "user_0001"))
            
        time.sleep(0.5)
        
        mock_post.assert_called()
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args[0]
        assert call_args[0] == sim.SIMULATOR_EPS_KEY
        assert isinstance(call_args[1], (int, float))
        assert sim.total_sent >= 100

def test_batch_sender_network_error():
    with patch("src.simulate_events.requests.post", side_effect=Exception("Connection refused")) as mock_post:
        # Reset queue
        while not sim.event_queue.empty():
            try:
                sim.event_queue.get_nowait()
            except:
                pass
                
        t = threading.Thread(target=sim.batch_sender, daemon=True)
        t.start()
        
        sim.event_queue.put(sim.make_event("product_viewed", sim.PRODUCTS[0], "user_0001"))
        
        time.sleep(0.5)
        mock_post.assert_called()
        # Should not crash the thread and successfully process the queue item (mark task as done)

def test_batch_sender_non_202_status():
    with patch("src.simulate_events.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        # Reset queue
        while not sim.event_queue.empty():
            try:
                sim.event_queue.get_nowait()
            except:
                pass
                
        t = threading.Thread(target=sim.batch_sender, daemon=True)
        t.start()
        
        sim.event_queue.put(sim.make_event("product_viewed", sim.PRODUCTS[0], "user_0001"))
        
        time.sleep(0.5)
        mock_post.assert_called()

def test_simulate_user_journey():
    # Reset queue
    while not sim.event_queue.empty():
        try:
            sim.event_queue.get_nowait()
        except:
            pass
            
    # Mock time.sleep in simulate_user_journey to speed it up
    with patch("src.simulate_events.time.sleep") as mock_sleep:
        t = threading.Thread(target=sim.simulate_user_journey, daemon=True)
        t.start()
        
        # Wait a moment for events to populate
        time.sleep(0.2)
        
        assert not sim.event_queue.empty()
        event = sim.event_queue.get()
        assert event["event_type"] in ["product_viewed", "cart_added", "purchase_completed", "payment_failed"]

def test_main():
    with patch("src.simulate_events.threading.Thread") as mock_thread, \
         patch("src.simulate_events.ThreadPoolExecutor") as mock_executor:
        
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        sim.main()
        
        assert mock_thread.call_count == 5
        assert mock_thread_instance.start.call_count == 5
        mock_executor.assert_called_once_with(max_workers=15)
