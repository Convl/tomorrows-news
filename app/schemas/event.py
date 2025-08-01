from datetime import datetime, timedelta
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from .extracted_event import ExtractedEventResponse


class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    date: datetime
    location: str | None = Field(None, max_length=300)
    significance: float = Field(..., ge=0.0, le=1.0)
    duration: timedelta | None = None
    additional_infos: Dict[str, str] | None = None


class EventCreate(EventBase):
    topic_id: int
    # Provenance fields for tracking which extracted event provided each field
    title_from_id: int | None = None
    description_from_id: int | None = None
    date_from_id: int | None = None
    location_from_id: int | None = None
    duration_from_id: int | None = None
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    semantic_vector: List[float] | None = None


class EventUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    date: datetime | None = None
    location: str | None = Field(None, max_length=300)
    significance: float | None = Field(None, ge=0.0, le=1.0)
    duration: timedelta | None = None
    additional_infos: Dict[str, str] | None = None
    # Provenance fields
    title_from_id: int | None = None
    description_from_id: int | None = None
    date_from_id: int | None = None
    location_from_id: int | None = None
    duration_from_id: int | None = None
    confidence_score: float | None = Field(None, ge=0.0, le=1.0)
    semantic_vector: List[float] | None = None


class EventResponse(EventBase):
    id: int
    # Provenance fields
    title_from_id: int | None = None
    description_from_id: int | None = None
    date_from_id: int | None = None
    location_from_id: int | None = None
    duration_from_id: int | None = None
    confidence_score: float
    semantic_vector: List[float] | None = None
    created_at: datetime
    update_history: List[datetime]
    topic_id: int
    extracted_events: List[ExtractedEventResponse] = []

    class Config:
        from_attributes = True


class EventSummary(BaseModel):
    """Lightweight event representation for lists"""

    id: int
    title: str
    date: datetime
    location: str | None = None
    significance: float

    class Config:
        from_attributes = True
