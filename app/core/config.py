from uuid import uuid4

from pydantic.types import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "loaded from .env file"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        "Sync version of the db url, needed for APScheduler"
        return self.DATABASE_URL.replace("+asyncpg", "")

    @property
    def PSYCOPG3_DATABASE_URL(self) -> str:
        """Plain PostgreSQL URL for LangGraph AsyncPostgresSaver (psycopg3)"""
        # Remove SQLAlchemy driver specification for psycopg3
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    @property
    def CONNECT_ARGS(self) -> dict:
        """Connection args for async SQLAlchemy engine, disables prepared statements if using Supabase transaction pooler"""
        # TODO: This may cause issues on DDL changes to e.g. Enums,
        # cf https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#prepared-statement-cache
        # cf https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#prepared-statement-name-with-pgbouncer
        # cf https://supabase.com/docs/guides/troubleshooting/disabling-prepared-statements-qL8lEL
        # cf https://github.com/supabase/supavisor/issues/287
        return (
            {
                "prepared_statement_cache_size": 0,
                "statement_cache_size": 0,
                "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
            }
            if "supabase.com:6543" in self.DATABASE_URL
            else {}
        )

    # App settings
    APP_NAME: str = "tomorrows-news"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    PYTHONASYNCIODEBUG: bool = False

    PROJECT_EMAIL: str
    PROJECT_EMAIL_PASSWORD: SecretStr
    PROJECT_EMAIL_FROM_NAME: str
    PROJECT_EMAIL_PORT: int
    PROJECT_EMAIL_HOST: str

    JWT_SECRET: SecretStr

    # API settings
    API_V1_STR: str = "/api/v1"

    # CORS settings
    CORS_ALLOW_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8000",
        "http://localhost:8001",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    OPENROUTER_API_KEY: SecretStr
    OPENROUTER_BASE_URL: str = ""

    OPENAI_API_KEY: SecretStr

    FIRECRAWL_API_KEY: SecretStr

    LANGSMITH_API_KEY: SecretStr
    LANGSMITH_TRACING: bool = True
    LANGSMITH_PROJECT: str = "tomorrows-news"

    TAVILY_API_KEY: SecretStr

    # Frontend URL for email links
    FRONTEND_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
