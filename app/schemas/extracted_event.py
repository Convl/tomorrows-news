from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class ExtractedEventResponse(BaseModel):
    """Schema for returning extracted event data"""

    id: int
    url: str
    title: str | None = None
    extraction_method: str | None = None
    extraction_metadata: Dict[str, Any] | None = None
    confidence_score: float | None = None
    found_at: datetime
    event_id: int

    class Config:
        from_attributes = True
