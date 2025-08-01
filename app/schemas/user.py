import uuid
from datetime import datetime
from typing import List

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr, Field


class UserRead(schemas.BaseUser[uuid.UUID]):
    username: str
    full_name: str | None = None
    created_at: datetime
    updated_at: datetime


class UserCreate(schemas.BaseUserCreate):
    username: str = Field(..., min_length=3, max_length=100)
    full_name: str | None = None


class UserUpdate(schemas.BaseUserUpdate):
    username: str | None = Field(None, min_length=3, max_length=100)
    full_name: str | None = None


# For backward compatibility with existing code
UserResponse = UserRead


class UserWithTopics(UserResponse):
    topics: List["TopicResponse"] = []

    class Config:
        from_attributes = True


# Import here to avoid circular imports
from .topic import TopicResponse

UserWithTopics.model_rebuild()
