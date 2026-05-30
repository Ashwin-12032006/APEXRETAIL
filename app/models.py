from typing import Optional
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime
from app.database import Base
from datetime import datetime

# --- Pydantic Schemas ---

class EventMetadataSchema(BaseModel):
    queue_depth: Optional[int] = None
    sku_zone: Optional[str] = None
    session_seq: Optional[int] = None
    attire: Optional[str] = None  # e.g. black_coat for staff uniform

class EventSchema(BaseModel):
    event_id: str = Field(..., description="UUID v4 globally unique identifier")
    store_id: str
    camera_id: str
    visitor_id: str
    event_type: str
    timestamp: str
    zone_id: Optional[str] = None
    dwell_ms: int = 0
    is_staff: bool = False
    confidence: float
    metadata: Optional[EventMetadataSchema] = None

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v):
        try:
            # Verify it's valid ISO 8601
            if v.endswith("Z"):
                datetime.fromisoformat(v.replace("Z", "+00:00"))
            else:
                datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("Timestamp must be in valid ISO-8601 UTC format (e.g. YYYY-MM-DDTHH:MM:SSZ)")

class TransactionSchema(BaseModel):
    store_id: str
    transaction_id: str
    timestamp: str
    basket_value_inr: float

# --- SQLAlchemy DB Models ---

class EventDB(Base):
    __tablename__ = "events"

    event_id = Column(String, primary_key=True, index=True)
    store_id = Column(String, index=True, nullable=False)
    camera_id = Column(String, nullable=False)
    visitor_id = Column(String, index=True, nullable=False)
    event_type = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    zone_id = Column(String, nullable=True)
    dwell_ms = Column(Integer, default=0)
    is_staff = Column(Boolean, default=False)
    confidence = Column(Float, nullable=False)
    
    # Flattened metadata fields
    queue_depth = Column(Integer, nullable=True)
    sku_zone = Column(String, nullable=True)
    session_seq = Column(Integer, nullable=True, default=1)

class TransactionDB(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True, index=True)
    store_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    basket_value_inr = Column(Float, nullable=False)
