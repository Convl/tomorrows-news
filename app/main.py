from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.worker.scheduler import scheduler
from rich.traceback import install

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
    from app.worker.scraper import Scraper
    scraper = Scraper(9)
    await scraper.scrape()
    # await scraper.test("Entscheidung des OVG Greifswald zum Festival in Jamel und Reaktion des Landkreises")