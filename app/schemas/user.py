import uuid
from datetime import datetime
from typing import List

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr, Field


class UserRead(schemas.BaseUser[uuid.UUID]):
    first_name: str
    last_name: str
    created_at: datetime
    updated_at: datetime


class UserCreate(schemas.BaseUserCreate):
    first_name: str
    last_name: str

class UserUpdate(schemas.BaseUserUpdate):
    first_name: str
    last_name: str
    updated_at: datetime = datetime.now()


class UserWithTopics(UserRead):
    topics: List["TopicResponse"] = []

    class Config:
        from_attributes = True


# Import here to avoid circular imports
from .topic import TopicResponse

UserWithTopics.model_rebuild()
