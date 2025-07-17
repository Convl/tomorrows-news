from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.event_source import EventSource
    from app.models.topic import Topic


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Generic event information
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    event_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # e.g., "hearing", "conference", "deadline", "announcement"

    # Flexible custom fields for domain-specific data
    custom_fields: Mapped[Dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # e.g., {"court_name": "District Court", "case_number": "ABC-123"}
    custom_fields_config: Mapped[Dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Configuration for which fields to use in deduplication
    # Example config: {"court_name": {"use_in_deduplication": true, "weight": 0.8}, "case_number": {"use_in_deduplication": true, "weight": 1.0}}

    # Source information
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Deduplication fields
    embedding_vector: Mapped[str | None] = mapped_column(Text, nullable=True)  # Store vector embedding as text
    similarity_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )  # For quick similarity checks

    # Status fields
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    duplicate_of_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("events.id"), nullable=True)

    # Metadata
    processing_notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # Notes from AI processing

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Foreign keys
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("topics.id"), nullable=False)

    # Relationships
    topic: Mapped["Topic"] = relationship("Topic", back_populates="events")
    event_sources: Mapped[List["EventSource"]] = relationship(
        "EventSource", back_populates="event", cascade="all, delete-orphan"
    )
    duplicate_of: Mapped["Event | None"] = relationship("Event", remote_side=[id], back_populates="duplicates")
    duplicates: Mapped[List["Event"]] = relationship(
        "Event", remote_side=[duplicate_of_id], back_populates="duplicate_of"
    )
