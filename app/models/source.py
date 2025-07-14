from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    base_url = Column(String(500), nullable=False)
    source_type = Column(String(50), nullable=False)  # e.g., "newspaper", "court_website", "rss"
    country = Column(String(100), nullable=True)
    language = Column(String(10), nullable=True)  # e.g., "de", "en"
    reliability_score = Column(Integer, default=50)  # 0-100 scale
    is_active = Column(Boolean, default=True)

    # Scraping configuration
    scraping_config = Column(JSON, nullable=True)  # Store scraping parameters
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    events = relationship("Event", back_populates="source")
