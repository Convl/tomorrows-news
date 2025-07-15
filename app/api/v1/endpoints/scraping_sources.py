from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.scraping_source import ScrapingSource
from app.models.topic import Topic
from app.schemas.scraping_source import ScrapingSourceCreate, ScrapingSourceResponse, ScrapingSourceUpdate

router = APIRouter()


@router.post("/", response_model=ScrapingSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_scraping_source(source: ScrapingSourceCreate, db: AsyncSession = Depends(get_db)):
    """Create a new scraping source"""
    # Validate topic exists
    if not (await db.execute(select(Topic).where(Topic.id == source.topic_id))).scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Topic not found")

    db_source = ScrapingSource(**source.model_dump())
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)
    return db_source


@router.get("/", response_model=List[ScrapingSourceResponse])
async def list_scraping_sources(*, skip: int = 0, limit: int = 100, topic_id: int, db: AsyncSession = Depends(get_db)):
    """List scraping sources for a specific topic with pagination"""
    sources = (
        (await db.execute(select(ScrapingSource).where(ScrapingSource.topic_id == topic_id).offset(skip).limit(limit)))
        .scalars()
        .all()
    )
    return sources


@router.get("/{source_id}", response_model=ScrapingSourceResponse)
async def get_scraping_source(source_id: int, db: AsyncSession = Depends(get_db)):
    """Get a scraping source by ID"""
    source = (await db.execute(select(ScrapingSource).where(ScrapingSource.id == source_id))).scalars().first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scraping source not found")
    return source


@router.put("/{source_id}", response_model=ScrapingSourceResponse)
async def update_scraping_source(
    source_id: int, source_update: ScrapingSourceUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a scraping source"""
    source = (await db.execute(select(ScrapingSource).where(ScrapingSource.id == source_id))).scalars().first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scraping source not found")

    # Update fields
    for field, value in source_update.model_dump(exclude_unset=True).items():
        setattr(source, field, value)

    await db.commit()
    await db.refresh(source)
    return source


@router.delete("/{source_id}")
async def delete_scraping_source(source_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a scraping source"""
    source = (await db.execute(select(ScrapingSource).where(ScrapingSource.id == source_id))).scalars().first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scraping source not found")

    await db.delete(source)
    await db.commit()
    return {"message": "Scraping source deleted successfully"}
