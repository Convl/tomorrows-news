import datetime
from typing import List

from apscheduler.triggers.interval import IntervalTrigger
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.status import HTTP_409_CONFLICT

from app.core.auth import current_active_non_demo_user, current_active_user
from app.database import get_db
from app.models.event import EventDB
from app.models.extracted_event import ExtractedEventDB
from app.models.scraping_source import ScrapingSourceDB
from app.models.topic import TopicDB
from app.models.user import UserDB
from app.models.websource import WebSourceDB
from app.schemas.scraping_source import ScrapingSourceCreate, ScrapingSourceResponse, ScrapingSourceUpdate
from app.worker.scheduler import scheduler

router = APIRouter()


@router.post("/", response_model=ScrapingSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_scraping_source(
    source: ScrapingSourceCreate,
    current_user: UserDB = Depends(current_active_non_demo_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new scraping source"""
    # Validate topic exists

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
    current_user: UserDB = Depends(current_active_non_demo_user),
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


@router.post("/{source_id}/trigger-scrape")
async def trigger_scrape(
    source_id: int,
    current_user: UserDB = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(ScrapingSourceDB)
        .join(TopicDB)
        .where(TopicDB.id == ScrapingSourceDB.topic_id)
        .where(ScrapingSourceDB.id == source_id)
    )
    if not current_user.is_superuser:
        query = query.where(TopicDB.user_id == current_user.id)
    source = (await db.execute(query)).scalars().first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scraping source not found")
    if source.currently_scraping:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail="Source is already being scraped.")
    # source.set_next_runtime(datetime.datetime.now()) does not work for some reason, so we need to delete and re-recreate
    source.remove_job()
    source.schedule_job(run_immediately=True)


@router.delete("/{source_id}")
async def delete_scraping_source(
    source_id: int,
    current_user: UserDB = Depends(current_active_non_demo_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a scraping source and clean up orphaned events"""
    log = f"Attempting to delete scraping source with id: {source_id} "

    query = (
        select(ScrapingSourceDB)
        .join(TopicDB, ScrapingSourceDB.topic_id == TopicDB.id)
        .where(ScrapingSourceDB.id == source_id)
    )

    if not current_user.is_superuser:
        query = query.where(TopicDB.user_id == current_user.id)

    source = (await db.execute(query)).scalars().first()
    if not source:
        log += "\n❌ ERROR: Scraping source not found or belongs to another user"
        logger.warning(log)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scraping source not found or belongs to another user"
        )

    affected_extracted_event_ids = (
        (await db.execute(select(ExtractedEventDB.id).where(ExtractedEventDB.scraping_source_id == source_id)))
        .scalars()
        .all()
    )
    log += f"\nIDS of ExtractedEvents that got deleted as a result: {', '.join(map(str, affected_extracted_event_ids))}"

    affected_web_source_ids = (
        (await db.execute(select(WebSourceDB.id).where(WebSourceDB.scraping_source_id == source_id))).scalars().all()
    )
    log += f"\nIDS of WebSources that got deleted as a result: {', '.join(map(str, affected_web_source_ids))}"

    # Get event IDs that may become orphaned after deletion
    event_ids_query = (
        select(ExtractedEventDB.event_id)
        .where(ExtractedEventDB.scraping_source_id == source_id, ExtractedEventDB.event_id.isnot(None))
        .distinct()
    )
    potentially_orphaned_event_ids = (await db.execute(event_ids_query)).scalars().all()
    orphaned_event_ids = []

    # Delete the scraping source and its jobs (cascades to extracted_events)
    source.remove_job()
    await db.delete(source)
    await db.flush()

    # For each potentially orphaned event, check if it has any remaining extracted_events. Delete if it doesnt.
    if potentially_orphaned_event_ids:
        for event_id in potentially_orphaned_event_ids:
            remaining_extracted_events = (
                await db.execute(select(func.count(ExtractedEventDB.id)).where(ExtractedEventDB.event_id == event_id))
            ).scalar()

            if remaining_extracted_events == 0:
                orphaned_event = (await db.execute(select(EventDB).where(EventDB.id == event_id))).scalars().first()
                if orphaned_event:
                    orphaned_event_ids.append(orphaned_event.id)
                    await db.delete(orphaned_event)

    await db.commit()

    log += f"\nIDS of Events that got deleted as a result: {', '.join(map(str, orphaned_event_ids))}"

    log += "\n✅ SUCCESS: Scraping source deleted successfully"
    logger.info(log)

    return {"message": log}
