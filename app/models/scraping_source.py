import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ScrapingSource(Base):
    """User-configured sources that should be monitored for relevant events"""

    __tablename__ = "scraping_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)  # "BBC Court News"
    base_url = Column(String(500), nullable=False)  # "https://bbc.com/news/court"
    source_type = Column(String(50), nullable=False)  # "webpage", "rss", "api"

    # Optional metadata
    country = Column(String(100), nullable=True)
    language = Column(String(10), nullable=True)  # "de", "en"
    description = Column(Text, nullable=True)

    # Configuration
    scraping_config = Column(JSON, nullable=True)  # Scraping parameters (selectors, etc.)
    scraping_frequency = Column(Integer, nullable=False, default=60)  # Frequency in minutes
    is_active = Column(Boolean, default=True)
    last_scraped_at = Column(DateTime(timezone=True), nullable=True, default=datetime.datetime(1900, 1, 1))

    # Topic relationship
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    topic = relationship("Topic", back_populates="scraping_sources")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
