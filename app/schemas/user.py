from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: str | None = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=100)
    full_name: str | None = None
    is_active: bool | None = None
    password: str | None = Field(None, min_length=8, max_length=100)


class UserResponse(UserBase):
    id: int
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserWithTopics(UserResponse):
    topics: List["TopicResponse"] = []

    class Config:
        from_attributes = True


# Import here to avoid circular imports
from .topic import TopicResponse

UserWithTopics.model_rebuild()
