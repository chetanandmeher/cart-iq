"""
CartIQ Stream Processor
Consumes events from Kafka and writes aggregates to Redis + raw events to PostgreSQL.
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from app.config import settings
from app.database import init_db
from app.aggregators import (
    update_revenue,
    update_top_products,
    update_event_counts,
    update_active_users,
    track_recent_events,
    save_to_db,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def process_event(event: dict):
    event_type = event.get("event_type", "unknown")
    user_id = event.get("user_id", "unknown")
    logger.info(f"Processing [{event_type}] for user {user_id}")

    update_event_counts(event)
    update_active_users(event)
    update_revenue(event)
    update_top_products(event)
    track_recent_events(event)
    save_to_db(event)


def create_consumer(retries: int = 10, delay: int = 5) -> KafkaConsumer:
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Connecting to Kafka (attempt {attempt}/{retries})...")
            consumer = KafkaConsumer(
                settings.kafka_topic,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id="cartiq-processor",
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda b: json.loads(b.decode("utf-8")),
            )
            logger.info("✅ Connected to Kafka successfully.")
            return consumer
        except NoBrokersAvailable:
            logger.warning(f"Kafka not ready. Retrying in {delay}s...")
            time.sleep(delay)
    raise RuntimeError("Could not connect to Kafka after retries.")


def run_consumer():
    init_db()
    consumer = create_consumer(retries=10, delay=5)
    executor = ThreadPoolExecutor(max_workers=20)
    logger.info("🚀 Consumer started — waiting for events...")

    for message in consumer:
        try:
            event = message.value
            executor.submit(process_event, event)
        except Exception as e:
            logger.error(f"Failed to submit message: {e}")


if __name__ == "__main__":
    run_consumer()