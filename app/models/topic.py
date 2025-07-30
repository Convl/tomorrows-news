from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.event import EventDB
    from app.models.extracted_event import ExtractedEventDB
    from app.models.scraping_source import ScrapingSourceDB
    from app.models.user import UserDB


class TopicDB(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON or comma-separated keywords for matching
    country: Mapped[str | None] = mapped_column(String(200), nullable=True)  # Country name or code as text
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Foreign key to user
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    user: Mapped["UserDB"] = relationship("UserDB", back_populates="topics", lazy="raise")
    events: Mapped[List["EventDB"]] = relationship(
        "EventDB", back_populates="topic", cascade="all, delete-orphan", lazy="raise"
    )
    extracted_events: Mapped[List["ExtractedEventDB"]] = relationship(
        "ExtractedEventDB", back_populates="topic", cascade="all, delete-orphan", lazy="raise"
    )
    scraping_sources: Mapped[List["ScrapingSourceDB"]] = relationship(
        "ScrapingSourceDB", back_populates="topic", cascade="all, delete-orphan", lazy="raise"
    )
