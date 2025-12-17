"""Authentication configuration for FastAPI-Users."""

import uuid

from fastapi import Depends, HTTPException, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.email import EmailService
from app.database import get_db, get_db_session
from app.models.user import UserDB
from app.schemas.user import UserCreate, UserRead, UserUpdate  # noqa: F401

# Strategy config (JWT)
SECRET = settings.JWT_SECRET.get_secret_value()
JWT_LIFETIME_SECONDS = settings.JWT_LIFETIME_SECONDS


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=JWT_LIFETIME_SECONDS)


# Transport config (Bearer)
bearer_transport = BearerTransport(tokenUrl=f"{settings.API_V1_STR}/auth/jwt/login")


# Authentication backend config (Strategy + Transport)
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


# User Manager config
class UserManager(UUIDIDMixin, BaseUserManager[UserDB, uuid.UUID]):
    """Custom user manager for additional logic."""

    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: UserDB, request: Request | None = None):
        """Called after a user registers."""
        logger.info("User <yellow>{user_id}</yellow> has registered.", user_id=user.id)

        # Automatically send verification email for new users
        if not user.is_verified:
            await self.request_verify(user, request)

    async def on_after_forgot_password(self, user: UserDB, token: str, request: Request | None = None):
        """Called after a user requests password reset."""
        logger.info(
            "User <yellow>{user_id}</yellow> has forgot their password. Reset token: <yellow>{token}</yellow>",
            user_id=user.id,
            token=token,
        )
        await EmailService.send_password_reset_email(user.email, token)

    async def on_after_request_verify(self, user: UserDB, token: str, request: Request | None = None):
        """Called after a user requests verification."""
        logger.info(
            "Verification requested for user <yellow>{user_id}</yellow>. Verification token: <yellow>{token}</yellow>",
            user_id=user.id,
            token=token,
        )
        await EmailService.send_verification_email(user.email, token)


# User / User Manager dependencies
async def get_user_db(session: AsyncSession = Depends(get_db)):
    """Get user database adapter."""
    yield SQLAlchemyUserDatabase(session, UserDB)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """Get user manager instance."""
    yield UserManager(user_db)


# FastAPI-Users instance
fastapi_users = FastAPIUsers[UserDB, uuid.UUID](get_user_manager, [auth_backend])

# Dependencies for current user
current_active_user = fastapi_users.current_user(active=True, verified=True)
current_superuser = fastapi_users.current_user(active=True, verified=True, superuser=True)


async def current_active_non_demo_user(user: UserDB = Depends(current_active_user)):
    if user.is_demo_user:
        raise HTTPException(status_code=403, detail="This method is not allowed for demo users")
    return user
