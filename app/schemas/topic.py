import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class TopicBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    keywords: str | None = None
    country: str | None = Field(None, max_length=200)  # Country name
    country_code: str | None = Field(None, max_length=10)  # ISO 3166-1 alpha-2
    is_active: bool = True


class TopicCreate(TopicBase):
    # user_id will be set automatically from current_user
    pass


class TopicUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    keywords: str | None = None
    country: str | None = Field(None, max_length=200)
    country_code: str | None = Field(None, max_length=10)
    is_active: bool | None = None


class TopicResponse(TopicBase):
    id: int
    user_id: uuid.UUID
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
