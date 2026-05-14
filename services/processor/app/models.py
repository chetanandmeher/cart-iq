from sqlalchemy import Column, String, Float, Integer, DateTime, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Event(Base):
    __tablename__ = "events"

    event_id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    product_id = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    extra_data = Column(JSON, nullable=True)