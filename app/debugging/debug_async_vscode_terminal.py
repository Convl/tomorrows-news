#!/usr/bin/env python3
"""
Quick debug commands
Usage: uv run python debug.py <command>
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select

from app.database import get_db_session
from app.models.scraping_source import ScrapingSourceDB
from app.worker.scraper import scraper


async def test_scraper(source_id: int = 5):
    """Test the scraper with a specific source ID"""
    print(f"Testing scraper with source_id={source_id}")
    await scraper._prepare_sources(source_id)


async def list_sources():
    """List all scraping sources"""
    async with get_db_session() as db:
        sources = (await db.execute(select(ScrapingSourceDB))).scalars().all()
        for source in sources:
            print(f"ID: {source.id}, Name: {source.name}, URL: {source.base_url}")


async def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "help"

    if command == "scraper":
        source_id = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        await test_scraper(source_id)
    elif command == "sources":
        await list_sources()
    elif command == "shell":
        # Drop into an async shell
        breakpoint()
    else:
        print("Available commands:")
        print("  uv run python debug.py scraper [source_id]  - Test scraper")
        print("  uv run python debug.py sources              - List sources")
        print("  uv run python debug.py shell                - Drop into debugger")


if __name__ == "__main__":
    asyncio.run(main())
