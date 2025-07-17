from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.event import Event


class EventSource(Base):
    """Represents a specific extraction of an event from a source URL"""

    __tablename__ = "event_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Where the event was found
    url: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)  # Specific URL
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Page/article title

    # Extraction metadata (specific to this event extraction)
    extraction_method: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "scraping", "api", "manual"
    extraction_metadata: Mapped[Dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # How THIS event was extracted
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # AI confidence for THIS extraction

    # When it was found
    found_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Foreign key to the event this source describes
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False)

    # Relationship back to the event
    event: Mapped["Event"] = relationship("Event", back_populates="event_sources")
