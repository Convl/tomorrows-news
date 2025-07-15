from fastapi import APIRouter

from app.api.v1.endpoints import events, scraping_sources, topics, users

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(topics.router, prefix="/topics", tags=["topics"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(scraping_sources.router, prefix="/scraping-sources", tags=["scraping-sources"])
