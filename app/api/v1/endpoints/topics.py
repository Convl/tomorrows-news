from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.topic import Topic
from app.schemas.topic import TopicCreate, TopicResponse, TopicUpdate

router = APIRouter()


@router.post("/", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(topic: TopicCreate, db: AsyncSession = Depends(get_db)):
    """Create a new topic"""
    # TODO: Implement topic creation logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Topic creation not implemented yet")


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(topic_id: int, db: AsyncSession = Depends(get_db)):
    """Get a topic by ID"""
    # TODO: Implement topic retrieval logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Topic retrieval not implemented yet")


@router.get("/", response_model=List[TopicResponse])
async def list_topics(skip: int = 0, limit: int = 100, user_id: int = None, db: AsyncSession = Depends(get_db)):
    """List topics with pagination and optional user filtering"""
    # TODO: Implement topic listing logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Topic listing not implemented yet")


@router.put("/{topic_id}", response_model=TopicResponse)
async def update_topic(topic_id: int, topic_update: TopicUpdate, db: AsyncSession = Depends(get_db)):
    """Update a topic"""
    # TODO: Implement topic update logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Topic update not implemented yet")


@router.delete("/{topic_id}")
async def delete_topic(topic_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a topic"""
    # TODO: Implement topic deletion logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Topic deletion not implemented yet")
