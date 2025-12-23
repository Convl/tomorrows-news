from datetime import datetime
from typing import TYPE_CHECKING, List

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.topic import TopicDB


class UserDB(Base, SQLAlchemyBaseUserTableUUID):
    __tablename__ = "users"

    # FastAPI-Users provides: id (UUID), email, hashed_password, is_active, is_superuser, is_verified
    # Additional custom fields
    # email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_demo_user: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    topics: Mapped[List["TopicDB"]] = relationship(
        "TopicDB",
        back_populates="user",
        cascade="save-update, merge, delete, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )
