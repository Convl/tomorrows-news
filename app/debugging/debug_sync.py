"""Debug utilities for development"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

sync_url = settings.DATABASE_URL
if not sync_url:
    raise ValueError("DATABASE_URL environment variable not set")

if sync_url.startswith("postgresql+asyncpg://"):
    sync_url = sync_url.replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(sync_url)


def gdbs():
    """Get a synchronous database session for debugging

    Usage in debug console:
        from app.core.debug import get_debug_session
        debug_db = get_debug_session()

        # Now use it like any SQLAlchemy session
        from app.models.scraping_source import ScrapingSource
        sources = debug_db.query(ScrapingSource).all()

        # Don't forget to close when done
        debug_db.close()
    """

    Session = sessionmaker(bind=engine)
    return Session()


def debug_scrape_sync(source_id: int):
    """Sync version for debugging - use this in debug console instead of await scraper.scrape()"""
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    from app.core.config import Settings
    from app.models.scraping_source import ScrapingSourceDB

    settings = Settings()
    # Create sync engine from async URL
    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url)
    Session = sessionmaker(engine)

    with Session() as session:
        source = (
            session.execute(select(ScrapingSourceDB).where(ScrapingSourceDB.id == source_id)).scalars().one_or_none()
        )
        if not source:
            print(f"Source with id {source_id} not found.")
            return
        print(f"Found source: {source}")
