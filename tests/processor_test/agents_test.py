import sys
from unittest.mock import MagicMock

# Mock faust module before importing src.agents
mock_faust = MagicMock()
mock_app = MagicMock()
mock_faust.App.return_value = mock_app

def mock_agent_decorator(*args, **kwargs):
    def decorator(func):
        return func
    return decorator

mock_app.agent = mock_agent_decorator
sys.modules['faust'] = mock_faust

import asyncio
import json
from unittest.mock import patch
from src.agents import process_event

def test_process_event_success():
    event_data = {"event_type": "purchase_completed", "user_id": "user-123"}
    raw_event = json.dumps(event_data).encode("utf-8")
    
    async def mock_stream():
        yield raw_event

    with patch("src.agents.update_event_counts") as mock_event_counts, \
         patch("src.agents.update_active_users") as mock_active_users, \
         patch("src.agents.update_revenue") as mock_revenue, \
         patch("src.agents.update_top_products") as mock_top_products, \
         patch("src.agents.track_recent_events") as mock_recent_events, \
         patch("src.agents.logger.info") as mock_log_info:

        asyncio.run(process_event(mock_stream()))

        mock_event_counts.assert_called_once_with(event_data)
        mock_active_users.assert_called_once_with(event_data)
        mock_revenue.assert_called_once_with(event_data)
        mock_top_products.assert_called_once_with(event_data)
        mock_recent_events.assert_called_once_with(event_data)
        mock_log_info.assert_called_once()


def test_process_event_exception():
    async def mock_stream():
        yield b"invalid-json-bytes"

    with patch("src.agents.logger.error") as mock_log_error:
        asyncio.run(process_event(mock_stream()))
        mock_log_error.assert_called_once()
        assert "Failed to process event" in mock_log_error.call_args[0][0]
