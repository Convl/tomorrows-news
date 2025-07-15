from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/events_db"

    @property
    def CONNECT_ARGS(self) -> dict:
        """Connection args for SQLAlchemy engine, disables prepared statements if using Supabase transaction pooler"""
        return {"prepared_statement_cache_size": 0} if "supabase.com:6543" in self.DATABASE_URL else {}

    # App settings
    APP_NAME: str = "Court Events API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
