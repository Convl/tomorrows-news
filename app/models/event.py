from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)

    # Generic event information
    location = Column(String(300), nullable=True)
    event_type = Column(String(100), nullable=True)  # e.g., "hearing", "conference", "deadline", "announcement"

    # Flexible custom fields for domain-specific data
    custom_fields = Column(JSON, nullable=True)  # e.g., {"court_name": "District Court", "case_number": "ABC-123"}
    custom_fields_config = Column(JSON, nullable=True)  # Configuration for which fields to use in deduplication
    # Example config: {"court_name": {"use_in_deduplication": true, "weight": 0.8}, "case_number": {"use_in_deduplication": true, "weight": 1.0}}

    # Source information
    source_url = Column(String(1000), nullable=True)

    # Deduplication fields
    embedding_vector = Column(Text, nullable=True)  # Store vector embedding as text
    similarity_hash = Column(String(64), nullable=True, index=True)  # For quick similarity checks
    confidence_score = Column(Float, default=0.0)  # AI confidence in the extraction

    # Status fields
    is_verified = Column(Boolean, default=False)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(Integer, ForeignKey("events.id"), nullable=True)

    # Metadata
    extracted_metadata = Column(JSON, nullable=True)  # Raw extraction data from AI
    processing_notes = Column(Text, nullable=True)  # Notes from AI processing

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Foreign keys
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)

    # Relationships
    topic = relationship("Topic", back_populates="events")
    source = relationship("Source", back_populates="events")
    duplicate_of = relationship("Event", remote_side=[id], backref="duplicates")
