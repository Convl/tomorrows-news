from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user, current_superuser
from app.database import get_db
from app.models.topic import TopicDB
from app.models.user import UserDB
from app.schemas.topic import TopicCreate, TopicResponse, TopicUpdate, TopicWithCounts

router = APIRouter()


@router.post("/", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(
    topic: TopicCreate, current_user: UserDB = Depends(current_active_user), db: AsyncSession = Depends(get_db)
):
    """Create a new topic for the current user"""
    # Create topic with current user's ID
    topic_data = topic.model_dump()
    topic_data["user_id"] = current_user.id

    db_topic = TopicDB(**topic_data)
    db.add(db_topic)
    await db.commit()
    await db.refresh(db_topic)
    return db_topic


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: int, current_user: UserDB = Depends(current_active_user), db: AsyncSession = Depends(get_db)
):
    """Get a topic by ID (only user's own topics or admin can access any)"""
    query = select(TopicDB).where(TopicDB.id == topic_id)

    # If not superuser, restrict to user's own topics
    if not current_user.is_superuser:
        query = query.where(TopicDB.user_id == current_user.id)

    topic = (await db.execute(query)).scalars().first()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    return topic


@router.get("/", response_model=List[TopicWithCounts])
async def list_topics(
    skip: int = 0,
    limit: int = 100,
    current_user: UserDB = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List topics for the current user (admins can see all)"""
    from app.models.event import EventDB
    from app.models.scraping_source import ScrapingSourceDB

    # Build query with counts
    query = (
        select(
            TopicDB, func.count(ScrapingSourceDB.id).label("source_count"), func.count(EventDB.id).label("event_count")
        )
        .outerjoin(ScrapingSourceDB, TopicDB.id == ScrapingSourceDB.topic_id)
        .outerjoin(EventDB, TopicDB.id == EventDB.topic_id)
        .group_by(TopicDB.id)
    )

    # If not superuser, restrict to user's own topics
    if not current_user.is_superuser:
        query = query.where(TopicDB.user_id == current_user.id)

    query = query.offset(skip).limit(limit)
    result = (await db.execute(query)).all()

    # Convert to TopicWithCounts
    topics_with_counts = []
    for row in result:
        topic, source_count, event_count = row
        topic_dict = {**topic.__dict__, "source_count": source_count, "event_count": event_count}
        topics_with_counts.append(TopicWithCounts(**topic_dict))

    return topics_with_counts


@router.put("/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: int,
    topic_update: TopicUpdate,
    current_user: UserDB = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a topic (only owner or admin)"""
    query = select(TopicDB).where(TopicDB.id == topic_id)

    # If not superuser, restrict to user's own topics
    if not current_user.is_superuser:
        query = query.where(TopicDB.user_id == current_user.id)

    topic = (await db.execute(query)).scalars().first()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    # Update topic with provided fields
    update_data = topic_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(topic, field, value)

    await db.commit()
    await db.refresh(topic)
    return topic


@router.delete("/{topic_id}")
async def delete_topic(
    topic_id: int, current_user: UserDB = Depends(current_active_user), db: AsyncSession = Depends(get_db)
):
    """Delete a topic and all its related data (only owner or admin)"""
    query = select(TopicDB).where(TopicDB.id == topic_id)

    # If not superuser, restrict to user's own topics
    if not current_user.is_superuser:
        query = query.where(TopicDB.user_id == current_user.id)

    topic = (await db.execute(query)).scalars().first()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    # Delete topic - cascade relationships will handle cleanup of:
    # - EventDB records (cascade="all, delete-orphan")
    # - ExtractedEventDB records (cascade="all, delete-orphan") 
    # - ScrapingSourceDB records (cascade="all, delete-orphan")
    # - WebSourceDB records (cascade="all, delete-orphan")
    await db.delete(topic)
    await db.commit()
    return {"message": "Topic deleted successfully"}
