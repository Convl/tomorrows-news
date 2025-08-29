from datetime import datetime, timedelta
from typing import Any, Dict, List

from pydantic import BaseModel, Field, field_validator


class ExtractedEventBase(BaseModel):
    """Base schema for extracted events"""

    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    date: datetime
    snippet: str = Field(..., min_length=1, max_length=500)

    @field_validator("snippet")
    def validate_snippet(cls, v: str) -> str:
        """Removes markdown-formatting from snippet to ensure it works when linking to url#:~:text=snippet"""
        # TODO: A function to match snippet to corresponding text of the full html of the source website 
        # (called during event extraction) would be more reliable, but this is good enough for now
        # [Bla](url) -> Bla
        import re
        v = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', v)
        # sometimes, the (url) is already gone, but the [] remain, although this of course will cause actual [] to not get highlighted
        v = re.sub(r'\[([^\]]+)\]', r'\1', v)

        if len(v) > 500:
            excess = len(v) - 500
            v = v[excess // 2 : -excess // 2]

        return v

    location: str | None = Field(None, max_length=300)
    significance: float = Field(..., ge=0.0, le=1.0)
    duration: timedelta | None = None
    additional_infos: Dict[str, str] | None = None
    # Source fields
    source_url: str = Field(..., max_length=1000)
    source_title: str | None = Field(None, max_length=500)
    source_published_date: datetime
    degrees_of_separation: int = Field(default=0, ge=0)



class ExtractedEventResponse(ExtractedEventBase):
    """Schema for returning extracted event data"""

    id: int
    created_at: datetime
    scraping_source_id: int
    topic_id: int
    event_id: int | None = None

    class Config:
        from_attributes = True
