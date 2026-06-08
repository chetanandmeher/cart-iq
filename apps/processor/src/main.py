"""
CartIQ Stream Processor
Consumes events from Kafka and writes aggregates to Redis + raw events to PostgreSQL.
Includes a Dead Letter Queue (DLQ) for safely handling malformed events.
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable
from src.config import settings
from src.database import init_db
from src.aggregators import (
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

# --- DLQ Setup ---
# Initialize a Producer specifically for the Dead Letter Queue
dlq_producer = KafkaProducer(
    bootstrap_servers=settings.kafka_bootstrap_servers,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)
DLQ_TOPIC = f"{settings.kafka_topic}_dlq"


def process_event(raw_message):
    """Processes raw bytes. Routes to DLQ on ANY failure."""
    try:
        # 1. Safe Decoding inside the thread
        event = json.loads(raw_message.value.decode("utf-8"))
        
        event_type = event.get("event_type", "unknown")
        user_id = event.get("user_id", "unknown")
        logger.info(f"Processing [{event_type}] for user {user_id}")

        # 2. Run Aggregators
        update_event_counts(event)
        update_active_users(event)
        update_revenue(event)
        update_top_products(event)
        track_recent_events(event)
        save_to_db(event)

    except Exception as e:
        # 3. Error Capture & DLQ Routing
        logger.error(f"Failed to process event. Routing to DLQ. Error: {str(e)}")
        
        dlq_payload = {
            "error": str(e),
            "original_message": raw_message.value.decode('utf-8', errors='replace'),
            "partition": getattr(raw_message, 'partition', None),
            "offset": getattr(raw_message, 'offset', None)
        }
        
        # Send to DLQ topic without crashing the worker
        dlq_producer.send(DLQ_TOPIC, value=dlq_payload)


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
                # NOTE: value_deserializer removed to consume raw bytes
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
    logger.info("🚀 Consumer started with DLQ enabled — waiting for events...")

    for message in consumer:
        try:
            # Pass the raw message to the thread pool instead of just the value
            executor.submit(process_event, message)
        except Exception as e:
            logger.error(f"Failed to submit message to thread pool: {e}")


if __name__ == "__main__":
    run_consumer()

    