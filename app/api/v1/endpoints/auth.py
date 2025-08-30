"""Authentication endpoints using FastAPI-Users."""

from app.core.auth import auth_backend, fastapi_users
from app.schemas.user import UserCreate, UserRead

# Authentication routes
auth_router = fastapi_users.get_auth_router(auth_backend, requires_verification=True)
register_router = fastapi_users.get_register_router(UserRead, UserCreate)
reset_password_router = fastapi_users.get_reset_password_router()
verify_router = fastapi_users.get_verify_router(UserRead)
