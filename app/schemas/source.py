from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class SourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    base_url: str = Field(..., max_length=500)
    source_type: str = Field(..., max_length=50)
    country: str | None = Field(None, max_length=100)
    language: str | None = Field(None, max_length=10)
    reliability_score: int = Field(50, ge=0, le=100)
    is_active: bool = True


class SourceCreate(SourceBase):
    scraping_config: Dict[str, Any] | None = None


class SourceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    base_url: str | None = Field(None, max_length=500)
    source_type: str | None = Field(None, max_length=50)
    country: str | None = Field(None, max_length=100)
    language: str | None = Field(None, max_length=10)
    reliability_score: int | None = Field(None, ge=0, le=100)
    is_active: bool | None = None
    scraping_config: Dict[str, Any] | None = None


class SourceResponse(SourceBase):
    id: int
    scraping_config: Dict[str, Any] | None = None
    last_scraped_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
