from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field

from app.core.enums import ScrapingSourceEnum


class ScrapingSourceBase(BaseModel):
    """Base schema for scraping sources"""

    name: str = Field(..., min_length=1, max_length=200)
    base_url: str = Field(..., max_length=500)
    source_type: ScrapingSourceEnum = Field(...)  # "webpage", "rss", "api"
    country: str | None = Field(None, max_length=100)
    language: str | None = Field(None, max_length=10)
    description: str | None = None
    degrees_of_separation: int = Field(default=0, ge=0, le=2)
    scraping_config: Dict[str, Any] | None = None
    scraping_frequency: int = Field(default=60000, ge=1)  # Frequency in minutes, minimum 1
    is_active: bool = True


class ScrapingSourceCreate(ScrapingSourceBase):
    """Schema for creating a scraping source"""

    topic_id: int  # Required when creating


class ScrapingSourceUpdate(BaseModel):
    """Schema for updating a scraping source"""

    name: str | None = Field(None, min_length=1, max_length=200)
    base_url: str | None = Field(None, max_length=500)
    source_type: str | None = Field(None, max_length=50)
    country: str | None = Field(None, max_length=100)
    language: str | None = Field(None, max_length=10)
    description: str | None = None
    degrees_of_separation: int = Field(default=0, ge=0, le=2)
    scraping_config: Dict[str, Any] | None = None
    scraping_frequency: int | None = Field(None, ge=1)  # Frequency in minutes, minimum 1
    is_active: bool | None = None


class ScrapingSourceResponse(ScrapingSourceBase):
    """Schema for returning scraping source data"""

    id: int
    topic_id: int
    last_scraped_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
