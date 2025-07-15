from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from .event_source import EventSourceResponse


class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    event_date: datetime
    location: str | None = Field(None, max_length=300)
    event_type: str | None = Field(None, max_length=100)
    source_url: str | None = Field(None, max_length=1000)


class EventCreate(EventBase):
    topic_id: int
    custom_fields: Dict[str, Any] | None = None
    custom_fields_config: Dict[str, Dict[str, Any]] | None = None


class EventUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    event_date: datetime | None = None
    location: str | None = Field(None, max_length=300)
    event_type: str | None = Field(None, max_length=100)
    source_url: str | None = Field(None, max_length=1000)
    is_verified: bool | None = None
    is_duplicate: bool | None = None
    duplicate_of_id: int | None = None
    custom_fields: Dict[str, Any] | None = None
    custom_fields_config: Dict[str, Dict[str, Any]] | None = None
    processing_notes: str | None = None


class EventResponse(EventBase):
    id: int
    similarity_hash: str | None = None
    is_verified: bool
    is_duplicate: bool
    duplicate_of_id: int | None = None
    custom_fields: Dict[str, Any] | None = None
    custom_fields_config: Dict[str, Dict[str, Any]] | None = None
    processing_notes: str | None = None
    created_at: datetime
    updated_at: datetime
    topic_id: int
    event_sources: List[EventSourceResponse] = []

    class Config:
        from_attributes = True


class EventSummary(BaseModel):
    """Lightweight event representation for lists"""

    id: int
    title: str
    event_date: datetime
    event_type: str | None = None
    is_verified: bool
    is_duplicate: bool

    class Config:
        from_attributes = True
