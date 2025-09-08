from fastapi import APIRouter

from app.api.v1.endpoints import auth, debug, events, scraping_sources, topics, users

api_router = APIRouter()

# Authentication routes
api_router.include_router(auth.auth_router, prefix="/auth/jwt", tags=["auth"])
api_router.include_router(auth.register_router, prefix="/auth", tags=["auth"])
api_router.include_router(auth.reset_password_router, prefix="/auth", tags=["auth"])
api_router.include_router(auth.verify_router, prefix="/auth", tags=["auth"])


# User management routes (protected)
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Business logic routes
api_router.include_router(topics.router, prefix="/topics", tags=["topics"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(scraping_sources.router, prefix="/scraping-sources", tags=["scraping-sources"])
api_router.include_router(debug.router, prefix="/debug", tags=["debug"])
