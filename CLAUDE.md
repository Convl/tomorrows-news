# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Environment Setup
```bash
# Install dependencies with uv
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your database connection details
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
# Run tests (if test framework is added)
pytest

# Run specific test file
pytest tests/test_specific.py
```

## Architecture Overview

This is a FastAPI-based court events tracking application with the following key architectural components:

### Core Structure
- **FastAPI**: Async web framework with automatic OpenAPI documentation
- **SQLAlchemy 2.0**: Async ORM for database operations
- **Pydantic**: Data validation and serialization
- **PostgreSQL with pgvector**: Database with vector similarity search capabilities
- **Alembic**: Database migrations

### Application Layout
```
app/
├── main.py              # FastAPI application entry point
├── database.py          # Database configuration and async session management
├── core/
│   └── config.py        # Settings management with pydantic-settings
├── models/              # SQLAlchemy database models
├── schemas/             # Pydantic models for API request/response
└── api/v1/
    ├── router.py        # Main API router
    └── endpoints/       # Individual endpoint modules
```

### Database Models
- **User**: User accounts with authentication fields
- **Topic**: Areas of interest belonging to users (e.g., "German Court Cases")
- **Event**: Events pertaining to a Topic of interest with deduplication support via embeddings and similarity hashing
- **Scraping Source**: News sources with scraping configuration
- **Event Source**: Source from which information abotu an event has been extracted

### Key Features
- **Event Deduplication**: Uses vector embeddings and similarity hashing
- **Flexible Event Data**: JSON fields for domain-specific custom data
- **Async Operations**: Full async support throughout the stack
- **Vector Search**: Prepared for pgvector similarity search implementation

## Configuration

Settings are managed through `app/core/config.py` using pydantic-settings:
- Loads from `.env` file automatically
- Key settings: DATABASE_URL, APP_NAME, DEBUG, API_V1_STR
- CORS configuration for cross-origin requests

## Database Schema

The application uses PostgreSQL with these key relationships:
- Users → Topics (one-to-many)
- Topics → Events (one-to-many)
- Sources → Events (one-to-many)
- Events → Events (self-referential for duplicates)

Events include advanced deduplication fields:
- `embedding_vector`: Vector embeddings for similarity search
- `similarity_hash`: Quick similarity comparison
- `custom_fields`: Flexible JSON storage for domain-specific data
- `duplicate_of_id`: Self-referential foreign key for duplicate detection

## Development Notes

- Uses async/await pattern throughout
- Database sessions are managed via dependency injection
- API endpoints follow REST conventions
- All models include created_at/updated_at timestamps
- Prepared for vector similarity search with pgvector extension
- Environment variables configured for database connection via Supabase

## Recent Architectural Decisions

### Source Model Separation (2025-01-15)
- **ScrapingSources**: User-configured sources to monitor
- **EventSources**: Auto-generated extraction records  
- **Relationship**: Event → EventSources (one-to-many)
- **Rationale**: Same event can be found from multiple sources with different confidence scores

### Event-Source Relationship
- Each EventSource represents a specific extraction of an event
- Confidence scores and extraction metadata are per-source
- Enables deduplication across multiple news sources