import json
from unittest.mock import patch, MagicMock, call
import pytest

# Setup global mock for KafkaProducer before importing main to prevent network access on import
import kafka
mock_producer_class = MagicMock()
mock_producer_instance = MagicMock()
mock_producer_class.return_value = mock_producer_instance
kafka.KafkaProducer = mock_producer_class

from src.main import process_event, create_consumer, run_consumer

def test_process_event_success():
    # Construct a raw Kafka message mock
    raw_message = MagicMock()
    event_data = {
        "event_type": "purchase_completed",
        "user_id": "user-123",
        "product_id": "prod-1",
        "product_name": "Product 1",
        "price": 100.0,
        "quantity": 2
    }
    raw_message.value = json.dumps(event_data).encode("utf-8")

    with patch("src.main.update_event_counts") as mock_event_counts, \
         patch("src.main.update_active_users") as mock_active_users, \
         patch("src.main.update_revenue") as mock_revenue, \
         patch("src.main.update_top_products") as mock_top_products, \
         patch("src.main.track_recent_events") as mock_recent_events, \
         patch("src.main.save_to_db") as mock_save_to_db:

        process_event(raw_message)

        mock_event_counts.assert_called_once_with(event_data)
        mock_active_users.assert_called_once_with(event_data)
        mock_revenue.assert_called_once_with(event_data)
        mock_top_products.assert_called_once_with(event_data)
        mock_recent_events.assert_called_once_with(event_data)
        mock_save_to_db.assert_called_once_with(event_data)


def test_process_event_failure_routes_to_dlq():
    raw_message = MagicMock()
    raw_message.value = b"invalid-json"
    raw_message.partition = 0
    raw_message.offset = 123

    # Reset mock producer send
    mock_producer_instance.send.reset_mock()

    with patch("src.main.update_event_counts") as mock_event_counts:
        # This will fail on json.loads
        process_event(raw_message)

        # Should NOT call aggregators
        mock_event_counts.assert_not_called()
        
        # Should call send on the DLQ producer
        mock_producer_instance.send.assert_called_once()
        args, kwargs = mock_producer_instance.send.call_args
        assert args[0] == "cartiq_events_dlq"
        dlq_payload = kwargs["value"]
        assert "error" in dlq_payload or "original_message" in dlq_payload
        assert dlq_payload["partition"] == 0
        assert dlq_payload["offset"] == 123


def test_create_consumer_success():
    mock_consumer_class = MagicMock()
    mock_consumer_instance = MagicMock()
    mock_consumer_class.return_value = mock_consumer_instance

    with patch("src.main.KafkaConsumer", mock_consumer_class):
        consumer = create_consumer(retries=3, delay=0.01)
        assert consumer == mock_consumer_instance
        mock_consumer_class.assert_called_once()


def test_create_consumer_retry_and_success():
    from kafka.errors import NoBrokersAvailable
    mock_consumer_class = MagicMock()
    mock_consumer_instance = MagicMock()
    
    # First call raises error, second succeeds
    mock_consumer_class.side_effect = [NoBrokersAvailable(), mock_consumer_instance]

    with patch("src.main.KafkaConsumer", mock_consumer_class), \
         patch("src.main.time.sleep") as mock_sleep:
        
        consumer = create_consumer(retries=3, delay=0.01)
        assert consumer == mock_consumer_instance
        assert mock_consumer_class.call_count == 2
        mock_sleep.assert_called_once_with(0.01)


def test_create_consumer_failure_all_retries():
    from kafka.errors import NoBrokersAvailable
    mock_consumer_class = MagicMock()
    mock_consumer_class.side_effect = NoBrokersAvailable()

    with patch("src.main.KafkaConsumer", mock_consumer_class), \
         patch("src.main.time.sleep") as mock_sleep:
        
        with pytest.raises(RuntimeError) as exc_info:
            create_consumer(retries=3, delay=0.01)
        
        assert "Could not connect to Kafka" in str(exc_info.value)
        assert mock_consumer_class.call_count == 3
        assert mock_sleep.call_count == 3


def test_run_consumer():
    mock_consumer = [MagicMock(), MagicMock()] # yield 2 messages
    mock_executor = MagicMock()

    with patch("src.main.init_db") as mock_init_db, \
         patch("src.main.create_consumer", return_value=mock_consumer) as mock_create_consumer, \
         patch("src.main.ThreadPoolExecutor", return_value=mock_executor) as mock_thread_pool, \
         patch("src.main.process_event") as mock_process_event:

        run_consumer()

        mock_init_db.assert_called_once()
        mock_create_consumer.assert_called_once_with(retries=10, delay=5)
        mock_thread_pool.assert_called_once_with(max_workers=20)
        
        # Verify submit called for both messages
        assert mock_executor.submit.call_count == 2
        
        # Check call arguments
        calls = mock_executor.submit.call_args_list
        assert calls[0] == call(mock_process_event, mock_consumer[0])
        assert calls[1] == call(mock_process_event, mock_consumer[1])


def test_run_consumer_submit_exception_handling():
    mock_consumer = [MagicMock()]
    mock_executor = MagicMock()
    # submit raises exception
    mock_executor.submit.side_effect = Exception("Submit queue full")

    with patch("src.main.init_db"), \
         patch("src.main.create_consumer", return_value=mock_consumer), \
         patch("src.main.ThreadPoolExecutor", return_value=mock_executor), \
         patch("src.main.logger.error") as mock_log_error:

        run_consumer()

        # Should log the submit exception and not crash the loop
        mock_log_error.assert_called_once()
        assert "Failed to submit message to thread pool" in mock_log_error.call_args[0][0]
