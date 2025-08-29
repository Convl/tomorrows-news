# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Environment Setup
```bash
# Install dependencies with uv
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your database connection details and API keys
```

### Database Operations
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check current migration status
alembic current
```

### Running the Application
```bash
# Start development server
uvicorn app.main:app --reload

# Access API documentation at: http://localhost:8000/api/v1/docs
# Health check endpoint: http://localhost:8000/health
# Frontend interface: http://localhost:8000/app/
```

### Code Quality
```bash
# Format code
ruff format

# Lint code
ruff check

# Fix linting issues
ruff check --fix
```

### Testing
```bash
# Run tests (when test framework is properly set up)
# Currently only has test_saver.py for LangGraph testing
python -m pytest app/tests/

# Run specific test file
python -m pytest app/tests/test_saver.py
```

## Architecture Overview

This is a FastAPI-based court events tracking and news monitoring application with intelligent deduplication and background scraping capabilities.

### Core Technology Stack
- **FastAPI**: Async web framework with automatic OpenAPI documentation
- **SQLAlchemy 2.0**: Async ORM with vector extension support
- **FastAPI-Users**: Complete user authentication system with UUID primary keys
- **PostgreSQL + pgvector**: Database with vector similarity search for event deduplication
- **APScheduler**: Background job scheduling for periodic scraping
- **LangChain/LangGraph**: LLM integration with PostgreSQL checkpointing
- **Pydantic**: Data validation and settings management
- **Alembic**: Database migrations

### Application Structure
```
app/
├── main.py                    # FastAPI app entry point with scheduler lifecycle
├── database.py               # Async database session management
├── core/
│   ├── config.py             # Settings with Supabase connection optimization
│   ├── auth.py               # FastAPI-Users authentication setup
│   └── email.py              # Email service integration
├── models/                   # SQLAlchemy models with async relationships
├── schemas/                  # Pydantic request/response models
├── api/v1/                   # REST API endpoints
├── worker/                   # Background processing system
│   ├── scheduler.py          # APScheduler with SQLAlchemy jobstore
│   ├── scraper.py           # News source scraping logic
│   └── scraping_workflow.py # LangGraph-based extraction workflows
└── debugging/               # Development utilities and debug tools
```

### Key Architectural Features

**User Management**: FastAPI-Users with UUID-based authentication, email verification, and password reset functionality.

**Event Deduplication System**: Events use vector embeddings and similarity hashing to detect and link duplicates across multiple news sources.

**Background Scraping**: APScheduler manages periodic scraping jobs with database persistence, configurable per-source frequencies, and LLM-powered content extraction.

**Multi-Source Tracking**: Separation between `ScrapingSources` (user-configured monitoring targets) and `EventSources` (extraction records), enabling confidence scoring and source attribution.

**Frontend Integration**: Static HTML/CSS/JS frontend served at `/app/` with REST API integration for user management and event monitoring.

**Database Optimizations**: Supabase-specific connection pooling, prepared statement cache management, and pgvector extension support.

## Configuration

Settings in `app/core/config.py` use pydantic-settings with `.env` loading:

**Database**: `DATABASE_URL` with automatic Supabase connection optimization
**Authentication**: `JWT_SECRET` for FastAPI-Users
**Email**: SMTP configuration for user verification and password reset
**LLM APIs**: OpenAI, OpenRouter, and Firecrawl API keys for content processing
**Monitoring**: LangSmith tracing and Tavily search integration
**CORS**: Configured for local development with multiple port support

## Database Schema

### Core Relationships
- **Users** (FastAPI-Users UUID) → **Topics** → **Events**
- **ScrapingSources** (user-configured) → **EventSources** (extraction records)  
- **Events** → **EventSources** (one-to-many for multi-source attribution)
- **Events** → **Events** (self-referential for duplicate detection)

### Advanced Features
- **pgvector integration**: Event embeddings for similarity search and deduplication
- **JSON custom fields**: Flexible domain-specific data storage per event
- **Confidence scoring**: Per-source extraction confidence and reliability metrics
- **Scheduled scraping**: APScheduler jobs with database persistence and failure handling

## Development Notes

**Async Throughout**: Full async/await pattern with SQLAlchemy 2.0 async sessions and dependency injection.

**LangGraph Integration**: Background workflows use PostgreSQL checkpointing with connection pooling considerations for Supabase.

**Job Scheduling**: APScheduler with SQLAlchemy jobstore supports dynamic job management via debug endpoints.

**Frontend Architecture**: Static frontend with vanilla JavaScript consuming REST APIs, no build process required.

**Vector Operations**: Prepared for pgvector similarity search with embedding storage and custom similarity functions.

## Recent Architectural Decisions

**FastAPI-Users Integration**: Migrated from custom auth to FastAPI-Users with UUID primary keys and comprehensive user management.

**Source Model Separation**: `ScrapingSources` for configuration vs `EventSources` for extraction records enables multi-source event attribution.

**LangGraph Workflows**: Event extraction uses persistent workflows with PostgreSQL checkpointing for reliability and resume capability.

**Frontend Simplification**: HTML/CSS/JS approach with no build system for rapid development and deployment.