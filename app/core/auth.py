"""Authentication configuration for FastAPI-Users."""

import os
import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.email import EmailService
from app.database import get_db
from app.models.user import UserDB
from app.schemas.user import UserCreate, UserRead, UserUpdate  # noqa: F401

# JWT Configuration
SECRET = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-this-in-production")
# Default to 30 days unless overridden by environment
JWT_LIFETIME_SECONDS = int(os.getenv("JWT_LIFETIME_SECONDS", "2592000"))

# Bearer transport (Authorization: Bearer <token>)
# Ensure tokenUrl matches the API prefix so Swagger "Authorize" works
bearer_transport = BearerTransport(tokenUrl=f"{settings.API_V1_STR}/auth/jwt/login")


# JWT Strategy
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=JWT_LIFETIME_SECONDS)


# Authentication backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


class UserManager(UUIDIDMixin, BaseUserManager[UserDB, uuid.UUID]):
    """Custom user manager for additional logic."""

    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: UserDB, request: Optional[Request] = None):
        """Called after a user registers."""
        print(f"User {user.id} has registered.")

        # Automatically send verification email for new users
        if not user.is_verified:
            try:
                await self.request_verify(user, request)
                print(f"Verification email sent to {user.email}")
            except Exception as e:
                print(f"Failed to send verification email to {user.email}: {e}")

    async def on_after_forgot_password(self, user: UserDB, token: str, request: Optional[Request] = None):
        """Called after a user requests password reset."""
        print(f"User {user.id} has forgot their password. Reset token: {token}")

        # Send password reset email
        success = await EmailService.send_password_reset_email(user.email, token)
        if success:
            print(f"Password reset email sent to {user.email}")
        else:
            print(f"Failed to send password reset email to {user.email}")

    async def on_after_request_verify(self, user: UserDB, token: str, request: Optional[Request] = None):
        """Called after a user requests verification."""
        print(f"Verification requested for user {user.id}. Verification token: {token}")

        # Send verification email
        success = await EmailService.send_verification_email(user.email, token)
        if success:
            print(f"Verification email sent to {user.email}")
        else:
            print(f"Failed to send verification email to {user.email}")


async def get_user_db(session: AsyncSession = Depends(get_db)):
    """Get user database adapter."""
    yield SQLAlchemyUserDatabase(session, UserDB)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """Get user manager instance."""
    yield UserManager(user_db)


# FastAPI-Users instance
fastapi_users = FastAPIUsers[UserDB, uuid.UUID](get_user_manager, [auth_backend])

# Dependencies for current user
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
