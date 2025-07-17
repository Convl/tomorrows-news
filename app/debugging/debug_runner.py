#!/usr/bin/env python3
"""
Debug runner script - use this to test async functions interactively
Run with: uv run python debug_runner.py
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select

from app.database import get_db_session
from app.models.scraping_source import ScrapingSource
from app.models.topic import Topic
from app.worker.scraper import scraper


async def main():
    """
    Main debug function - put your test code here or call it interactively
    Set breakpoints in this function to get into the debugger with full async context
    """

    # Example usage - uncomment what you want to test:

    # Test database access
    # async with get_db_session() as db:
    #     sources = (await db.execute(select(ScrapingSource))).scalars().all()
    #     print(f"Found {len(sources)} sources")

    # Test scraper
    # await scraper.scrape(5)

    # Test other async functions
    # ...

    # Set a breakpoint HERE to get into debugger with full async context
    print("Debug runner ready - set breakpoints in this function and call async code!")
    breakpoint()  # This will drop you into the debugger

    print("Debug session complete")


if __name__ == "__main__":
    asyncio.run(main())
