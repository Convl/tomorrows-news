from datetime import datetime, timedelta
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ExtractedEventBase(BaseModel):
    """Base schema for extracted events"""

    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    date: datetime
    location: str | None = Field(None, max_length=300)
    significance: float = Field(..., ge=0.0, le=1.0)
    duration: timedelta | None = None
    additional_infos: Dict[str, str] | None = None
    # Source fields
    source_url: str = Field(..., max_length=1000)
    source_title: str | None = Field(None, max_length=500)
    source_published_date: datetime
    degrees_of_separation: int = Field(default=0, ge=0)


class ExtractedEventCreate(ExtractedEventBase):
    """Schema for creating an extracted event"""

    scraping_source_id: int
    topic_id: int
    semantic_vector: List[float] | None = None


class ExtractedEventUpdate(BaseModel):
    """Schema for updating an extracted event"""

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    date: datetime | None = None
    location: str | None = Field(None, max_length=300)
    significance: float | None = Field(None, ge=0.0, le=1.0)
    duration: timedelta | None = None
    additional_infos: Dict[str, str] | None = None
    source_url: str | None = Field(None, max_length=1000)
    source_title: str | None = Field(None, max_length=500)
    source_published_date: datetime | None = None
    degrees_of_separation: int | None = Field(None, ge=0)
    semantic_vector: List[float] | None = None
    event_id: int | None = None


class ExtractedEventResponse(ExtractedEventBase):
    """Schema for returning extracted event data"""

    id: int
    created_at: datetime
    semantic_vector: List[float] | None = None
    scraping_source_id: int
    topic_id: int
    event_id: int | None = None

    class Config:
        from_attributes = True


class ExtractedEventSummary(BaseModel):
    """Lightweight extracted event representation for lists"""

    id: int
    title: str
    date: datetime
    source_url: str
    significance: float
    event_id: int | None = None

    class Config:
        from_attributes = True
