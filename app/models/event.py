from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.worker.scraping_models import AdditionalInfo

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
    duration: Mapped[str | None] = mapped_column(String(100), nullable=True)
    additional_infos: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)

    @property
    def additional_infos_list(self) -> list[AdditionalInfo] | None:
        """Convert JSON back to list[AdditionalInfo]."""
        return [AdditionalInfo(**item) for item in self.additional_infos] if self.additional_infos else None

    @additional_infos_list.setter
    def additional_infos_list(self, value: list[AdditionalInfo] | None):
        """Convert list[AdditionalInfo] to JSON for storage."""
        self.additional_infos = [item.model_dump() for item in value] if value else None

    # Provenance fields. Title and description may be composites. Location and duration are optional.
    title_from_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("extracted_events.id"), nullable=True)
    description_from_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("extracted_events.id"), nullable=True)
    date_from_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("extracted_events.id"), nullable=True)
    location_from_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("extracted_events.id"), nullable=True)
    duration_from_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("extracted_events.id"), nullable=True)

    # Confidence
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)

    # Vector embedding for deduplication and similarity search
    semantic_vector: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    update_history: Mapped[list[datetime]] = mapped_column(JSON, nullable=False, default=list)

    # Topic (parent)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("topics.id"), nullable=False)
    topic: Mapped["TopicDB"] = relationship("TopicDB", back_populates="events")

    # Extracted Events (children)
    extracted_events: Mapped[list["ExtractedEventDB"]] = relationship(
        "ExtractedEventDB",
        back_populates="event",
        cascade="all, delete-orphan",
        foreign_keys="ExtractedEventDB.event_id",
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
