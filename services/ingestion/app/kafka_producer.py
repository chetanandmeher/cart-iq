import json
import logging
from datetime import datetime
from kafka import KafkaProducer
from app.config import settings

logger = logging.getLogger(__name__)

_producer = None


def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=json_serializer).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",
            retries=3,
        )
    return _producer


async def publish_event(event: dict) -> bool:
    try:
        producer = get_producer()
        future = producer.send(
            topic=settings.kafka_topic,
            value=event,
            key=event.get("user_id"),
        )
        producer.flush()
        logger.info(f"Event published: {event['event_type']} for user {event['user_id']}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")
        return False