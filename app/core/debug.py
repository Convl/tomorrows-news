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
