"""
CartIQ Stream Processor
Consumes events from Kafka and writes aggregates to Redis.
Uses kafka-python (pure Python, no C compilation needed).
"""

import json
import logging
import threading
from kafka import KafkaConsumer
from app.config import settings
from app.aggregators import (
    update_revenue,
    update_top_products,
    update_event_counts,
    update_active_users,
    track_recent_events,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def process_event(event: dict):
    """Process a single event — update all Redis aggregates."""
    event_type = event.get("event_type", "unknown")
    user_id = event.get("user_id", "unknown")
    logger.info(f"Processing [{event_type}] for user {user_id}")

    update_event_counts(event)
    update_active_users(event)
    update_revenue(event)
    update_top_products(event)
    track_recent_events(event)


def run_consumer():
    """Start Kafka consumer loop. Blocks forever."""
    logger.info(f"Connecting to Kafka at {settings.kafka_bootstrap_servers}")
    logger.info(f"Subscribing to topic: {settings.kafka_topic}")

    consumer = KafkaConsumer(
        settings.kafka_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="cartiq-processor",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
    )

    logger.info("✅ Consumer started — waiting for events...")

    for message in consumer:
        try:
            event = message.value
            process_event(event)
        except Exception as e:
            logger.error(f"Failed to process message: {e}")


if __name__ == "__main__":
    run_consumer()