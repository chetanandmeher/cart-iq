import logging
from fastapi import APIRouter, HTTPException
from app.schemas import CartEvent
from app.kafka_producer import publish_event

logger = logging.getLogger(__name__)

router = APIRouter()


from typing import Union, List

@router.post("/events", status_code=202)
async def ingest_event(event_data: Union[CartEvent, List[CartEvent]]):
    events = event_data if isinstance(event_data, list) else [event_data]
    
    failed_count = 0
    for event in events:
        success = await publish_event(event.dict())
        if not success:
            failed_count += 1

    if failed_count == len(events):
        raise HTTPException(
            status_code=500,
            detail="Failed to publish all events to Kafka"
        )

    return {
        "status": "accepted",
        "processed": len(events),
        "failed": failed_count
    }


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "ingestion"}