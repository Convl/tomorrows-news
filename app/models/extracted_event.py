from datetime import date, datetime, time, timezone, timedelta
from typing import TYPE_CHECKING, Any, Dict

import pytz
from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, Interval
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.event import EventDB
    from app.models.scraping_source import ScrapingSourceDB
    from app.models.topic import TopicDB
    from app.worker.scraping_models import ExtractedEvent


class ExtractedEventDB(Base):
    """Represents a specific extraction of an event from a source URL"""

    __tablename__ = "extracted_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Fields that mirror ExtractedEvent as extracted by the worker
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    significance: Mapped[float] = mapped_column(Float, nullable=False)
    duration: Mapped[timedelta | None] = mapped_column(Interval, nullable=True)
    additional_infos: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)

    # Fields that mirror the WebSource from which the ExtractedEvent was extracted
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_published_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    degrees_of_separation: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Vector embeddings for deduplication and similarity search
    semantic_vector: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)

    # Scraping Source which led to this extraction:
    scraping_source_id: Mapped[int] = mapped_column(Integer, ForeignKey("scraping_sources.id"), nullable=False)
    scraping_source: Mapped["ScrapingSourceDB"] = relationship(
        "ScrapingSourceDB", back_populates="extracted_events", lazy="raise"
    )

    # Topic which this extracted event belongs to
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("topics.id"), nullable=False)
    topic: Mapped["TopicDB"] = relationship("TopicDB", back_populates="extracted_events", lazy="raise")

    # The consolidated event, create from this ExtractedEvent and others
    event_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("events.id"), nullable=True)
    event: Mapped["EventDB"] = relationship(
        "EventDB", back_populates="extracted_events", foreign_keys=[event_id], lazy="raise"
    )

    @classmethod
    def from_extracted_event(
        cls, extracted_event: "ExtractedEvent", scraping_source: "ScrapingSourceDB", event_id: int | None = None
    ) -> "ExtractedEventDB":
        """Convert Pydantic ExtractedEvent to SQLAlchemy ExtractedEventDB."""

        # Get all the base event fields, handle the nested source
        event_data = extracted_event.model_dump()
        source_data = event_data.pop("source")

        # If event only has a date and no time, set it to midnight
        event_date = event_data.pop("date")
        if isinstance(event_date, date) and not isinstance(event_date, datetime):
            event_date = datetime.combine(event_date, time(0, 0, 0))

        # Localize event date to the timezone of the country where the event takes place, or UTC as a fallback
        event_country_code = event_data.pop("country_code")
        event_country_timezone = timezone.utc
        try:
            # try getting timezone from country as inferred by LLM
            event_countries_list = pytz.country_timezones[event_country_code.upper()]
            event_country_timezone = pytz.timezone(event_countries_list[0])
        except Exception:
            # if that fails, try getting timezone from country as inferred by ScrapingSource
            if scraping_source.country:
                try:
                    event_countries_list = pytz.country_timezones[scraping_source.country.upper()]
                    event_country_timezone = pytz.timezone(event_countries_list[0])
                except Exception:
                    pass
            else:
                pass

        if event_date.tzinfo:
            event_date = event_date.replace(tzinfo=None)
        event_date = event_country_timezone.localize(event_date)

        # Localize source published date to UTC
        source_published_date = source_data["date"]
        if source_published_date.tzinfo is None:
            # Assume naive dates are UTC
            source_published_date = source_published_date.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC
            source_published_date = source_published_date.astimezone(timezone.utc)

        return cls(
            **event_data,
            date=event_date,
            source_url=source_data["url"],
            source_title=source_data["title"],
            source_published_date=source_published_date,
            degrees_of_separation=source_data["degrees_of_separation"],
            scraping_source_id=scraping_source.id,
            topic_id=scraping_source.topic_id,
            event_id=event_id,
        )
