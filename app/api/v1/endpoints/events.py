from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import current_active_user
from app.database import get_db
from app.models.event import EventDB
from app.models.topic import TopicDB
from app.models.user import UserDB
from app.schemas.event import EventCreate, EventResponse, EventSummary, EventUpdate

router = APIRouter()


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate, db: AsyncSession = Depends(get_db)):
    """Create a new event"""
    # TODO: Implement event creation logic with deduplication
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Event creation not implemented yet")


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    current_user: UserDB = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get an event by ID with its extracted events, enforcing access control"""
    query = select(EventDB).options(selectinload(EventDB.extracted_events)).where(EventDB.id == event_id)

    event = (await db.execute(query)).scalars().first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    # Access control: non-admins can only access events under their own topics
    if not current_user.is_superuser:
        topic_check = (
            (
                await db.execute(
                    select(TopicDB.id).where(and_(TopicDB.id == event.topic_id, TopicDB.user_id == current_user.id))
                )
            )
            .scalars()
            .first()
        )
        if not topic_check:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this event")

    return event


@router.get("/", response_model=List[EventResponse])
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    topic_id: Optional[int] = Query(None),
    verified_only: bool = Query(False),
    exclude_duplicates: bool = Query(True),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    include_extracted: bool = Query(False),
    current_user: UserDB = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List events with filtering and pagination.

    Notes:
    - Upcoming events by default: from_date defaults to now UTC minus 2 hours
    - Ordered by ascending event date
    - Access control: non-admins see only events under their own topics
    - include_extracted controls whether extracted events are eagerly loaded; for simplicity and to avoid lazy-load errors,
      we always eager-load extracted events in the response model.
    """

    # Default window: small look-back buffer (2 hours)
    if from_date is None:
        from_date = datetime.now(timezone.utc) - timedelta(hours=2)

    # Base query
    query = select(EventDB)

    # Access control and topic scoping
    if topic_id is not None:
        # Verify access to the topic if not admin
        if not current_user.is_superuser:
            allowed = (
                (
                    await db.execute(
                        select(TopicDB.id).where(and_(TopicDB.id == topic_id, TopicDB.user_id == current_user.id))
                    )
                )
                .scalars()
                .first()
            )
            if not allowed:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this topic")
        query = query.where(EventDB.topic_id == topic_id)
    else:
        # If no topic is provided, non-admins see only their topics' events
        if not current_user.is_superuser:
            user_topic_ids_subq = select(TopicDB.id).where(TopicDB.user_id == current_user.id)
            query = query.where(EventDB.topic_id.in_(user_topic_ids_subq))

    # Date window
    conditions = [EventDB.date >= from_date]
    if to_date is not None:
        conditions.append(EventDB.date <= to_date)
    if conditions:
        query = query.where(and_(*conditions))

    # Ordering and pagination
    query = query.order_by(EventDB.date.asc()).offset(skip).limit(limit)

    events = (await db.execute(query)).scalars().all()

    if include_extracted:
        # Eager load extracted events for these rows
        # Refetch with selectinload to avoid N+1
        ids = [e.id for e in events]
        if not ids:
            return []
        loaded = (
            (
                await db.execute(
                    select(EventDB)
                    .options(selectinload(EventDB.extracted_events))
                    .where(EventDB.id.in_(ids))
                    .order_by(EventDB.date.asc())
                )
            )
            .scalars()
            .all()
        )
        return loaded
    else:
        # Build responses without accessing relationship to avoid lazy-load errors
        from app.schemas.event import EventResponse  # local import to avoid cycles at module import time

        results: List[EventResponse] = []
        for e in events:
            results.append(
                EventResponse(
                    id=e.id,
                    title=e.title,
                    description=e.description,
                    date=e.date,
                    location=e.location,
                    significance=e.significance,
                    duration=e.duration,
                    additional_infos=e.additional_infos,
                    title_from_id=e.title_from_id,
                    description_from_id=e.description_from_id,
                    date_from_id=e.date_from_id,
                    location_from_id=e.location_from_id,
                    duration_from_id=e.duration_from_id,
                    confidence_score=e.confidence_score,
                    created_at=e.created_at,
                    update_history=e.update_history,
                    topic_id=e.topic_id,
                    extracted_events=[],  # empty by default when not including
                )
            )
        return results


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(event_id: int, event_update: EventUpdate, db: AsyncSession = Depends(get_db)):
    """Update an event"""
    # TODO: Implement event update logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Event update not implemented yet")


@router.delete("/{event_id}")
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an event"""
    # TODO: Implement event deletion logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Event deletion not implemented yet")


@router.get("/similar/{event_id}", response_model=List[EventSummary])
async def find_similar_events(event_id: int, limit: int = Query(10, le=50), db: AsyncSession = Depends(get_db)):
    """Find similar events for deduplication purposes"""
    # TODO: Implement similarity search using vector embeddings
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Similar event search not implemented yet")


@router.post("/{event_id}/verify")
async def verify_event(event_id: int, db: AsyncSession = Depends(get_db)):
    """Mark an event as verified"""
    # TODO: Implement event verification logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Event verification not implemented yet")
