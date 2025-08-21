import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from rich.traceback import install

from app.api.v1.router import api_router
from app.core.config import settings
from app.worker.scheduler import scheduler

if settings.DEBUG:
    install(show_locals=True)

logging.getLogger("asyncio").setLevel(logging.ERROR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "openapi_json": f"{settings.API_V1_STR}/openapi.json",
    }


@app.get("/debug")
async def dbg():
    print("debug entry hit")

    # List scheduler jobs
    from datetime import timezone

    from app.worker.scheduler import scheduler

    job_infos = []
    for job in scheduler.get_jobs():  # or scheduler.get_jobs(jobstore="scraping")
        job_info = {
            "id": job.id,
            "name": job.name,
            "func": f"{job.func.__module__}.{job.func.__name__}",
            "args": job.args,
            "trigger": str(job.trigger),
            "next_run_time": job.next_run_time.astimezone(timezone.utc).isoformat() if job.next_run_time else None,
            "misfire_grace_time": job.misfire_grace_time,
            "coalesce": job.coalesce,
            "max_instances": job.max_instances,
            "executor": job.executor,
        }
        job_infos.append(job_info)
        print(job_info)

    return {"jobs": job_infos}


@app.get("/debug/reschedule/{job_id}/{minutes}")
async def reschedule_job(job_id: str, minutes: int):
    """Manually reschedule a job to run in X minutes from now"""
    from datetime import datetime, timedelta

    from app.worker.scheduler import scheduler

    try:
        # Calculate the target time
        next_run_time = datetime.now() + timedelta(minutes=minutes)

        # Get the job
        job = scheduler.get_job(job_id, jobstore="scraping")

        if not job:
            return {"error": f"Job '{job_id}' not found!", "success": False}

        old_next_run = job.next_run_time

        # Modify the job's next run time
        scheduler.modify_job(job_id=job_id, jobstore="scraping", next_run_time=next_run_time)

        # Verify the change
        updated_job = scheduler.get_job(job_id, jobstore="scraping")

        return {
            "success": True,
            "job_id": job_id,
            "old_next_run_time": old_next_run.isoformat() if old_next_run else None,
            "new_next_run_time": updated_job.next_run_time.isoformat() if updated_job.next_run_time else None,
            "minutes_from_now": minutes,
            "message": f"Job '{job_id}' will run in {minutes} minutes",
        }

    except Exception as e:
        return {"error": str(e), "success": False}


# Mount static frontend at /app
app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")
