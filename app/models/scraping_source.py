import datetime
from typing import TYPE_CHECKING, Any, Dict

import apscheduler
from apscheduler.job import Job
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, event
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.enums import ScrapingSourceEnum, get_enum_values
from app.database import Base

if TYPE_CHECKING:
    from app.models.topic import Topic


class ScrapingSource(Base):
    """User-configured sources that should be monitored for relevant events"""

    __tablename__ = "scraping_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)  # "BBC Court News"
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)  # "https://bbc.com/news/court"
    source_type: Mapped[ScrapingSourceEnum] = mapped_column(
        SqlEnum(ScrapingSourceEnum, values_callable=get_enum_values), nullable=False
    )

    # Optional metadata
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)  # "de", "en"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Configuration
    scraping_config: Mapped[Dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Scraping parameters (selectors, etc.)
    scraping_frequency: Mapped[int] = mapped_column(Integer, nullable=False, default=60)  # Frequency in minutes
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_scraped_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=datetime.datetime(1900, 1, 1)
    )

    # Topic relationship
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("topics.id"), nullable=False)
    topic: Mapped["Topic"] = relationship("Topic", back_populates="scraping_sources")

    # Timestamps
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    jobstore : str = "scraping"

    @property
    def job_id(self) -> str:
        """Generate consistent job ID for this scraping source"""
        if not self.id:
            # TODO: Make sure this can't actually happen
            raise Exception("Scraping Source id is None. Perhaps the Scraping Source got deleted, and now the deletion of its job has failed?")
        return f"scraping_source_{self.id}"
    
    def schedule_job(self):
        """Schedule job for this source if it is active"""
        # Only schedule if source is active
        if self.is_active:
            from app.worker.scheduler import scheduler
            from app.worker.scraper import scraper
            from apscheduler.triggers.interval import IntervalTrigger
            scheduler.add_job(
                func=scraper.scrape,
                args=[self.id],
                trigger=IntervalTrigger(minutes=self.scraping_frequency),
                id=self.job_id,
                jobstore=self.jobstore,
                replace_existing=True
            )
    
    def remove_job(self):
        """Remove the scheduled job for this source"""
        from app.worker.scheduler import scheduler
        
        try:
            scheduler.remove_job(self.job_id, jobstore=self.jobstore)
        except Exception:
            pass
    
    def update_job(self):
        """Update job only if necessary"""
        from app.worker.scheduler import scheduler
        from apscheduler.triggers.interval import IntervalTrigger
        
        try:
            if not (existing_job := scheduler.get_job(self.job_id, jobstore=self.jobstore)):
                self.schedule_job()
                return
            elif not self.is_active:
                scheduler.remove_job(self.job_id, jobstore=self.jobstore)
                return

            if existing_job.trigger.interval.total_seconds() != self.scraping_frequency * 60:
                scheduler.reschedule_job(
                    job_id=self.job_id,
                    jobstore=self.jobstore, 
                    trigger=IntervalTrigger(minutes=self.scraping_frequency),
                )
        except Exception as e:
            self.remove_job()
            self.schedule_job()
            raise e
    

# SQLAlchemy event listeners to automatically manage jobs
@event.listens_for(ScrapingSource, 'after_insert')
def schedule_job_after_insert(mapper, connection, target: ScrapingSource):
    target.schedule_job()


@event.listens_for(ScrapingSource, 'after_update')
def update_job_after_update(mapper, connection, target: ScrapingSource):
    """Automatically update job after ScrapingSource is modified"""
    # Check if relevant fields changed
    state = target.__dict__
    history = state.get('_sa_instance_state')
    
    if history and history.attrs:
        changed_fields = {key for key in ['scraping_frequency', 'is_active'] 
                         if key in history.attrs and history.attrs[key].history.has_changes()}
        
        if changed_fields:
            target.update_job()


@event.listens_for(ScrapingSource, 'after_delete')
def remove_job_after_delete(mapper, connection, target: ScrapingSource):
    """Automatically remove job after ScrapingSource is deleted"""
    # Not sure if the commit will destroy the target (or set its id to None), so best to grab the id / jobstore before
    # and use a custom function below instead of calling a delete_job method on the target
    target.remove_job()
    # job_id = target.job_id
    # jobstore = target.jobstore
    # @event.listens_for(connection, 'after_commit', once=True)
    # def remove_job():
    #     from app.worker.scheduler import scheduler
    #     try:
    #         scheduler.remove_job(job_id=job_id, jobstore=jobstore)
    #     except Exception:
    #         pass