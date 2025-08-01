from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class TopicBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    keywords: str | None = None
    country: str | None = Field(None, max_length=200)
    language: str | None = Field(None, max_length=10)
    is_active: bool = True


class TopicCreate(TopicBase):
    user_id: int


class TopicUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    keywords: str | None = None
    country: str | None = Field(None, max_length=200)
    language: str | None = Field(None, max_length=10)
    is_active: bool | None = None


class TopicResponse(TopicBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TopicWithEvents(TopicResponse):
    events: List["EventResponse"] = []

    class Config:
        from_attributes = True


# Import here to avoid circular imports
from .event import EventResponse

TopicWithEvents.model_rebuild()
