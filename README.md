# Tomorrow's News

An intelligent events tracking and news monitoring application that automatically scrapes news sources, extracts upcoming events using LLM workflows, and deduplicates similar events using vector embeddings.

## What It Does

- **Monitors News Sources**: Automatically scrapes configured news sources for upcoming events pertaining to the user's topic of interest
- **Intelligent Extraction**: Uses LangChain/LangGraph workflow with LLM integration to extract structured event data
- **Smart Deduplication**: Employs PostgreSQL + pgvector for vector similarity search to detect and link duplicate events across sources
- **Background Processing**: APScheduler manages periodic scraping jobs with database persistence and failure handling
- **User Management**: Complete authentication system with FastAPI-Users
- **Multi-Source Attribution**: Tracks every source that contributed information to an extracted event

## Disclaimer

This project, to me, is really about the backend. For the frontend, I wanted to quickly get something functional, so I vibe-coded it. The backend, however, is 100% coded by hand.

## Tech Stack

**Backend**:
- FastAPI with async/await throughout
- SQLAlchemy 2.0 + PostgreSQL + pgvector
- LangChain/LangGraph for LLM workflows
- APScheduler for background jobs
- FastAPI-Users for authentication
- Alembic for database migrations
- Newspaper4k / Feedparser for scraping
- Loguru for logging

**Frontend**:
- Vanilla HTML/CSS/JavaScript
- No build system, served statically
- REST API integration

