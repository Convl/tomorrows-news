# Tomorrow's News

An intelligent events tracking and news monitoring application that automatically scrapes news sources, extracts upcoming events using LLM workflows, and deduplicates similar events using vector embeddings. Presented via React with React Router / React Router / Material UI.

## What It Does

- **Monitors News Sources**: Automatically scrapes configured news sources for upcoming events pertaining to the user's topic of interest
- **Intelligent Extraction**: Uses LangChain/LangGraph workflow with LLM integration to extract structured event data
- **Smart Deduplication**: Employs PostgreSQL + pgvector for vector similarity search to detect and link duplicate events across sources
- **Background Processing**: APScheduler manages periodic scraping jobs with database persistence and failure handling
- **Live Updates**: Server-sent events ensure the frontend stays up to date when scraping jobs run
- **User Management**: Complete authentication system with FastAPI-Users
- **Multi-Source Attribution**: Tracks every source that contributed information to an extracted event

## Disclaimer

I only recently started learning React, so the frontend is about 50/50 hand-written/AI-generated (albeit under close supervision and with manual verification / integration). The backend, on the other hand, is 100% hand-written, with AI-use limited to explaining concepts / helping to track down bugs and similar assistive tasks.

## Tech Stack

**Backend**:

- FastAPI with async/await throughout
- SQLAlchemy 2.0 + PostgreSQL + pgvector
- SSE for live updates to the frontend
- LangChain/LangGraph for LLM workflows
- APScheduler for background jobs
- FastAPI-Users for authentication
- Alembic for database migrations
- Newspaper4k / Feedparser for scraping
- Loguru for logging

**Frontend**:

- React / React Router for presentation
- Tanstack Query + Axios for API interactions
- Fetch Event Source for Auth Header support in SSE
