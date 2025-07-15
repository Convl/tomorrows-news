from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class EventSource(Base):
    """Represents a specific extraction of an event from a source URL"""

    __tablename__ = "event_sources"

    id = Column(Integer, primary_key=True, index=True)

    # Where the event was found
    url = Column(String(1000), nullable=False, index=True)  # Specific URL
    title = Column(String(500), nullable=True)  # Page/article title

    # Extraction metadata (specific to this event extraction)
    extraction_method = Column(String(50), nullable=True)  # "scraping", "api", "manual"
    extraction_metadata = Column(JSON, nullable=True)  # How THIS event was extracted
    confidence_score = Column(Float, nullable=True)  # AI confidence for THIS extraction

    # When it was found
    found_at = Column(DateTime(timezone=True), server_default=func.now())

    # Foreign key to the event this source describes
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    # Relationship back to the event
    event = relationship("Event", back_populates="event_sources")
