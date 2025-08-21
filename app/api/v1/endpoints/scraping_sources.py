from typing import List

from apscheduler.triggers.interval import IntervalTrigger
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import current_active_user
from app.database import get_db
from app.models.scraping_source import ScrapingSourceDB
from app.models.topic import TopicDB
from app.models.user import UserDB
from app.schemas.scraping_source import ScrapingSourceCreate, ScrapingSourceResponse, ScrapingSourceUpdate
from app.worker.scheduler import scheduler

router = APIRouter()


@router.post("/", response_model=ScrapingSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_scraping_source(
    source: ScrapingSourceCreate,
    current_user: UserDB = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new scraping source"""
    # Validate topic exists
    print("test")
    topic = (
        (
            await db.execute(
                select(TopicDB).options(selectinload(TopicDB.scraping_sources)).where(TopicDB.id == source.topic_id)
            )
        )
        .scalars()
        .first()
    )

    if not topic:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Topic not found")

    # Enforce ownership unless superuser
    if not current_user.is_superuser and topic.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this topic")

    # Validate no duplicate ScrapingSources get entered. TODO: Take care of cases like http://abc.com vs http://abc.com/
    if any(
        present_source.base_url == source.base_url and present_source.source_type == source.source_type
        for present_source in topic.scraping_sources
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source with this source_type and base_url already exists for this topic.",
        )

    db_source = ScrapingSourceDB(**source.model_dump())
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)
    return db_source


@router.get("/", response_model=List[ScrapingSourceResponse])
async def list_scraping_sources(
    *,
    skip: int = 0,
    limit: int = 100,
    topic_id: int,
    current_user: UserDB = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List scraping sources for a specific topic with pagination"""
    # Validate topic and ownership
    topic = (await db.execute(select(TopicDB).where(TopicDB.id == topic_id))).scalars().first()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    if not current_user.is_superuser and topic.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this topic")

    sources = (
        (
            await db.execute(
                select(ScrapingSourceDB).where(ScrapingSourceDB.topic_id == topic_id).offset(skip).limit(limit)
            )
        )
        .scalars()
        .all()
    )

    return sources


@router.get("/{source_id}", response_model=ScrapingSourceResponse)
async def get_scraping_source(
    source_id: int,
    current_user: UserDB = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a scraping source by ID"""
    # Enforce ownership by joining with Topic
    query = (
        select(ScrapingSourceDB)
        .join(TopicDB, ScrapingSourceDB.topic_id == TopicDB.id)
        .where(ScrapingSourceDB.id == source_id)
    )
    if not current_user.is_superuser:
        query = query.where(TopicDB.user_id == current_user.id)
    source = (await db.execute(query)).scalars().first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scraping source not found")
    return source


@router.put("/{source_id}", response_model=ScrapingSourceResponse)
async def update_scraping_source(
    source_id: int,
    source_update: ScrapingSourceUpdate,
    current_user: UserDB = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a scraping source"""
    # Load and enforce ownership
    query = (
        select(ScrapingSourceDB)
        .join(TopicDB, ScrapingSourceDB.topic_id == TopicDB.id)
        .where(ScrapingSourceDB.id == source_id)
    )
    if not current_user.is_superuser:
        query = query.where(TopicDB.user_id == current_user.id)
    source = (await db.execute(query)).scalars().first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scraping source not found")

    # Update fields
    for field, value in source_update.model_dump(exclude_unset=True).items():
        setattr(source, field, value)

    await db.commit()
    await db.refresh(source)
    return source


@router.delete("/{source_id}")
async def delete_scraping_source(
    source_id: int,
    current_user: UserDB = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a scraping source"""
    # Load and enforce ownership
    query = (
        select(ScrapingSourceDB)
        .join(TopicDB, ScrapingSourceDB.topic_id == TopicDB.id)
        .where(ScrapingSourceDB.id == source_id)
    )
    if not current_user.is_superuser:
        query = query.where(TopicDB.user_id == current_user.id)
    source = (await db.execute(query)).scalars().first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scraping source not found")

    await db.delete(source)
    await db.commit()
    return {"message": "Scraping source deleted successfully"}
