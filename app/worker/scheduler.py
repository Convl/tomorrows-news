from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
from sqlalchemy import create_engine

from app.core.config import settings

scheduler_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    # Recycle the connection to avoid connection issues.
    # See:
    # - https://github.com/orgs/supabase/discussions/27071
    pool_recycle=240,
    # Pre-ping the connection to avoid connecting to a closed connection.
    # See:
    # - https://github.com/orgs/supabase/discussions/27071
    pool_pre_ping=True,
    # Do not expire sessions on commit.
    # See:
    # - https://github.com/sqlalchemy/sqlalchemy/discussions/11495
)
jobstore = {"scraping": SQLAlchemyJobStore(engine=scheduler_engine)}
executors = {"scraping": AsyncIOExecutor()}

job_defaults = {
    "coalesce": True,  # Combine multiple missed executions into one
    "misfire_grace_time": 691200,  # Allow jobs to be executed up to 8 days late
}

scheduler = AsyncIOScheduler(jobstores=jobstore, executors=executors, job_defaults=job_defaults, timezone=datetime.timezone.utc)
