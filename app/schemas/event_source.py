from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class EventSourceCreate(BaseModel):
    """Schema for creating an event source"""

    url: str = Field(..., max_length=1000)
    title: str | None = Field(None, max_length=500)
    extraction_method: str | None = Field(None, max_length=50)
    extraction_metadata: Dict[str, Any] | None = None
    confidence_score: float | None = Field(None, ge=0.0, le=1.0)
    event_id: int


class EventSourceResponse(BaseModel):
    """Schema for returning event source data"""

    id: int
    url: str
    title: str | None = None
    extraction_method: str | None = None
    extraction_metadata: Dict[str, Any] | None = None
    confidence_score: float | None = None
    found_at: datetime
    event_id: int

    class Config:
        from_attributes = True
