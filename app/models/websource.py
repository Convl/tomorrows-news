from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.scraping_source import ScrapingSourceDB
    from app.models.topic import TopicDB


class WebSourceDB(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    published_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Scraping Source which this source belongs to
    # TODO: nullable should really be False for the scraping_source_id. Setting it to True for now though, to ensure it works with exisiting db entries
    scraping_source_id: Mapped[int] = mapped_column(Integer, ForeignKey("scraping_sources.id"), nullable=True) 
    scraping_source: Mapped["ScrapingSourceDB"] = relationship("ScrapingSourceDB", back_populates="sources", lazy="raise")

    # Topic which this source belongs to
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("topics.id"), nullable=False)
    topic: Mapped["TopicDB"] = relationship("TopicDB", back_populates="sources", lazy="raise")
