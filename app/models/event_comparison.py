from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.event import EventDB
from app.models.extracted_event import ExtractedEventDB


class EventComparisonDB(Base):
    """Records the comparison between an ExtractedEventDB and EventDB for analysis purposes"""

    __tablename__ = "event_comparisons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # References to the compared events
    extracted_event_id: Mapped[int] = mapped_column(Integer, ForeignKey("extracted_events.id", ondelete="CASCADE"), nullable=False)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)

    # Event data at time of comparison
    extracted_event_title: Mapped[str] = mapped_column(String(500), nullable=False)
    extracted_event_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_title: Mapped[str] = mapped_column(String(500), nullable=False)
    event_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Comparison metrics
    vector_similarity: Mapped[float] = mapped_column(Float, nullable=False)
    vector_threshold_met: Mapped[bool] = mapped_column(Boolean, nullable=False)
    llm_considers_same_event: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    extracted_event: Mapped["ExtractedEventDB"] = relationship("ExtractedEventDB", lazy="raise")
    event: Mapped["EventDB"] = relationship("EventDB", lazy="raise")
