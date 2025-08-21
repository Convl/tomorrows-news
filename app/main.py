import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
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
    # from sqlalchemy import delete
    # from app.database import get_db_session
    # from app.models import EventComparisonDB, EventDB, ExtractedEventDB
    from app.worker.scraper import Scraper
    from datetime import timezone
    from app.worker.scheduler import scheduler

    for job in scheduler.get_jobs():  # or scheduler.get_jobs(jobstore="scraping")
        print({
            "id": job.id,
            "name": job.name,
            "trigger": str(job.trigger),
            "next_run_time": job.next_run_time.astimezone(timezone.utc).isoformat() if job.next_run_time else None,
        })
    print("henlo")

    # Clear test data before running scraper
    # async with get_db_session() as db:
    #     await db.execute(delete(EventComparisonDB))
    #     await db.execute(delete(ExtractedEventDB))
    #     await db.execute(delete(EventDB))
    #     await db.commit()
    #     print("Cleared all EventDB, ExtractedEventDB, and EventComparisonDB records")

    # scraper = Scraper(13)
    # await scraper.scrape()


# Mount static frontend at /app
app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")

