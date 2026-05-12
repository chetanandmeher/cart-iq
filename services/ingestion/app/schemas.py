from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional
import uuid


class EventType(str, Enum):
    product_viewed = "product_viewed"
    cart_added = "cart_added"
    cart_removed = "cart_removed"
    purchase_completed = "purchase_completed"
    payment_failed = "payment_failed"


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