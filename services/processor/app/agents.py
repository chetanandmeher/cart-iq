import json
import logging
import faust

from app.config import settings
from app.enums import EventType
from app.aggregators import (
    update_revenue,
    update_top_products,
    update_event_counts,
    update_active_users,
    track_recent_events,
)

logger = logging.getLogger(__name__)

app = faust.App(
    "cartiq-processor",
    broker=f"kafka://{settings.kafka_bootstrap_servers}",
    value_serializer="raw",
)

events_topic = app.topic(settings.kafka_topic, value_type=bytes)


@app.agent(events_topic)
async def process_event(stream):
    async for raw_event in stream:
        try:
            event = json.loads(raw_event)
            logger.info(f"Processing event: {event.get('event_type')} for user {event.get('user_id')}")

            update_event_counts(event)
            update_active_users(event)
            update_revenue(event)
            update_top_products(event)
            track_recent_events(event)

        except Exception as e:
            logger.error(f"Failed to process event: {e}")