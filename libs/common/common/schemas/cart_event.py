from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid
from common.enums import EventType


class CartEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    user_id: str
    product_id: str
    product_name: str
    price: float
    quantity: int = 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = {}

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
