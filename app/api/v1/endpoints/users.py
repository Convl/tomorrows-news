from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import UserDB
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user"""

    if (await db.execute(select(UserDB).where(UserDB.email == user.email))).scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")

    user_data = user.model_dump(exclude={"password"})
    user_data["hashed_password"] = "mock password hash"  # TODO integrate password hashing
    db_user = UserDB(**user_data)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get a user by ID"""
    # TODO: Implement user retrieval logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="User retrieval not implemented yet")


@router.get("/", response_model=List[UserResponse])
async def list_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """List all users, up to the limit"""
    users = (await db.execute(select(UserDB).offset(skip).limit(limit))).scalars().all()
    return users


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_db)):
    """Update a user"""
    # TODO: Implement user update logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="User update not implemented yet")


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a user"""
    # TODO: Implement user deletion logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="User deletion not implemented yet")
