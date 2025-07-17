#!/usr/bin/env python3
"""
Start IPython with async support and pre-loaded app modules
Run with: uv run python debug_ipython.py
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Pre-import commonly used modules
import asyncio

from sqlalchemy import select

from app.database import get_db_session
from app.models.scraping_source import ScrapingSource
from app.models.topic import Topic
from app.worker.scraper import scraper


def start_ipython():
    """Start IPython with async support and pre-loaded modules"""
    from IPython import start_ipython as ipython_start

    # Enable async support
    from IPython.core.magic import register_line_magic

    print("🐍 Starting IPython with async support...")
    print("📦 Pre-loaded modules:")
    print("   - get_db_session, scraper, ScrapingSource, Topic, select, asyncio")
    print("✨ Use 'await' directly in the REPL!")
    print("💡 Example: await scraper.scrape(5)")

    # Create a namespace with our modules
    user_ns = {
        "get_db_session": get_db_session,
        "scraper": scraper,
        "ScrapingSource": ScrapingSource,
        "Topic": Topic,
        "select": select,
        "asyncio": asyncio,
    }

    # Start IPython with async support
    ipython_start(argv=["--autocall=2"], user_ns=user_ns)


if __name__ == "__main__":
    start_ipython()
