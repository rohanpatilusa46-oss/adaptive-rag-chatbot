from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = Field(default="development", description="Application environment name")

    # Backend
    api_prefix: str = "/api"
    cors_allow_origins: List[AnyHttpUrl] | List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/live_ai_assistant",
        description="SQLAlchemy database URL",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for cache/session",
    )

    # LLM / external APIs
    llm_api_key: str | None = Field(default=None, description="API key for LLM provider")
    llm_api_base: str | None = Field(default=None, description="Base URL for LLM provider")
    search_api_key: str | None = Field(default=None, description="API key for search provider")
    search_api_base: str | None = Field(
        default="https://api.tavily.com",
        description="Base URL for search provider (Tavily by default)",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Application log level")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

