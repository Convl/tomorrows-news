from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, Interval, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.extracted_event import ExtractedEventDB
    from app.models.topic import TopicDB


class EventDB(Base):
    """The consolidated version of all ExtractedEvents for a given real-world event."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Fields that mirror ExtractedEvent
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    significance: Mapped[float] = mapped_column(Float, nullable=False)
    duration: Mapped[timedelta | None] = mapped_column(Interval, nullable=True)
    additional_infos: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)

    # Provenance fields. Title and description may be composites. Location and duration are optional.
    title_from_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("extracted_events.id", ondelete="SET NULL"), nullable=True
    )
    description_from_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("extracted_events.id", ondelete="SET NULL"), nullable=True
    )
    date_from_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("extracted_events.id", ondelete="SET NULL"), nullable=True
    )
    location_from_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("extracted_events.id", ondelete="SET NULL"), nullable=True
    )
    duration_from_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("extracted_events.id", ondelete="SET NULL"), nullable=True
    )

    # Confidence
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)

    # Vector embedding for deduplication and similarity search
    semantic_vector: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    update_history: Mapped[list[datetime]] = mapped_column(JSON, nullable=False, default=list)

    # Topic (parent)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    topic: Mapped["TopicDB"] = relationship("TopicDB", back_populates="events", lazy="raise")

    # Extracted Events (children)
    extracted_events: Mapped[list["ExtractedEventDB"]] = relationship(
        "ExtractedEventDB",
        back_populates="event",
        cascade="save-update, merge, delete",
        passive_deletes=True,
        foreign_keys="ExtractedEventDB.event_id",
        lazy="raise",
    )

    @classmethod
    def from_extracted_event_db(cls, extracted_event_db: "ExtractedEventDB") -> "EventDB":
        """Convert Pydantic ExtractedEvent to SQLAlchemy EventDB."""
        return cls(
            title=extracted_event_db.title,
            description=extracted_event_db.description,
            date=extracted_event_db.date,
            location=extracted_event_db.location,
            significance=extracted_event_db.significance,
            duration=extracted_event_db.duration,
            additional_infos=extracted_event_db.additional_infos,
            semantic_vector=extracted_event_db.semantic_vector,
            topic_id=extracted_event_db.topic_id,
        )
