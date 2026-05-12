import logging
from fastapi import APIRouter, HTTPException
from app.schemas import CartEvent
from app.kafka_producer import publish_event

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/events", status_code=202)
async def ingest_event(event: CartEvent):
    success = await publish_event(event.dict())

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to publish event to Kafka"
        )

    return {
        "status": "accepted",
        "event_id": event.event_id,
        "event_type": event.event_type,
    }


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "ingestion"}