import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user
from app.database import get_db, get_db_session
from app.models import ExtractedEventDB
from app.models.user import UserDB
from app.worker.scheduler import scheduler

router = APIRouter()


@router.get("/frontend")
async def debug_frontend():
    await asyncio.sleep(3)
    return {"message": "Connection to backend established"}


@router.post("/trigger-job/{source_id}")
async def debug_trigger_job(source_id: int):
    """Trigger a job for a scraping source"""
    job_id = f"scraping_source_{source_id}"
    scheduler.modify_job(job_id, next_run_time=datetime.now(timezone.utc) + timedelta(seconds=30))
    return {"message": f"Job {job_id} scheduled to run in 30 seconds"}


@router.get("/get-jobs")
async def get_jobs():
    """Get all jobs"""
    jobs = scheduler.get_jobs()
    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "max_instances": job.max_instances,
        }
        for job in jobs
    ]


@router.delete("/delete-scraping-job/{source_id}")
async def delete_scraping_job(source_id: int):
    """Delete a scraping job for a scraping source"""
    scheduler.remove_job(job_id=f"scraping_source_{source_id}", jobstore="scraping")
    return {"message": f"Job {f'scraping_source_{source_id}'} deleted"}


@router.get("/get-magic-link")
async def get_magic_link(
    user_email: str,
    lifetime_seconds: int = 0,
    url: str = "https://tomorrows-news.vercel.app/login",
    db: AsyncSession = Depends(get_db),
):
    if not (target_user := (await db.execute(select(UserDB).where(UserDB.email == user_email))).scalar_one_or_none()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_email} not found")

    from fastapi_users.authentication import JWTStrategy

    from app.core.config import settings

    jwt_strategy = JWTStrategy(secret=settings.JWT_SECRET.get_secret_value(), lifetime_seconds=lifetime_seconds)
    token = await jwt_strategy.write_token(target_user)

    separator = "&" if "?" in url else "?"
    return f"{url}{separator}token={token}"


@router.get("/")
async def dbg(current_user: UserDB = Depends(current_active_user), db: AsyncSession = Depends(get_db)):
    """Debug endpoint, used for testing various things"""
    logger.info("This <red>is</red> a <yellow>test</yellow> message")
