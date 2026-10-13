"""
Core application configuration.

All settings are loaded from environment variables with sensible defaults.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Locate and load .env from backend directory, root directory, or current working directory
_core_dir = os.path.dirname(os.path.abspath(__file__))
_app_dir = os.path.dirname(_core_dir)
_backend_dir = os.path.dirname(_app_dir)
_root_dir = os.path.dirname(_backend_dir)

_env_file_candidates = [
    os.path.join(_root_dir, ".env"),
    os.path.join(_backend_dir, ".env"),
    os.path.join(os.getcwd(), ".env"),
]
for _env_candidate in _env_file_candidates:
    if os.path.isfile(_env_candidate):
        load_dotenv(_env_candidate, override=False)


class Settings(BaseSettings):
    """Application-wide settings loaded strictly from environment variables / .env file."""

    # ── Application ──────────────────────────────────────────────────────────
    app_env: str = Field(default="development")
    app_name: str = Field(default="Dynamic AI Chatbot")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    app_debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/app.log")
    enable_file_logging: bool = Field(default=True)

    # ── Google Gemini ────────────────────────────────────────────────────────
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="")

    # ── Database ─────────────────────────────────────────────────────────────
    # Database URL is strictly loaded from DATABASE_URL in .env
    database_url: str = Field(default="")

    # ── Redis ────────────────────────────────────────────────────────────────
    # Redis URL is strictly loaded from REDIS_URL in .env
    redis_url: str = Field(default="")

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_origins: str = Field(default="")

    # ── Security ─────────────────────────────────────────────────────────────
    # Secret key is strictly loaded from SECRET_KEY in .env
    secret_key: str = Field(default="")
    rate_limit_per_minute: int = Field(default=30)
    max_message_length: int = Field(default=5000)

    # ── AI Settings ──────────────────────────────────────────────────────────
    default_temperature: float = Field(default=0.7)
    max_context_messages: int = Field(default=20)
    max_response_tokens: int = Field(default=2048)
    enable_streaming: bool = Field(default=True)
    enable_rag: bool = Field(default=True)
    enable_tools: bool = Field(default=True)

    # ── Vector Store (PostgreSQL pgvector) ───────────────────────────────────
    embedding_model: str = Field(default="")
    vector_dimension: int = Field(default=384)

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_demo_mode(self) -> bool:
        """True when no Gemini API key is configured."""
        return not self.gemini_api_key

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def async_database_url(self) -> str:
        """Normalize database URL for asyncpg and cloud providers (Neon, Supabase, Render)."""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if "sslmode=require" in url:
            url = url.replace("sslmode=require", "ssl=require")
        # Strip libpq-only params (e.g., channel_binding) unsupported by asyncpg
        if "channel_binding=" in url:
            import re
            url = re.sub(r"[&?]channel_binding=[^&]+", "", url)
        return url

    model_config = SettingsConfigDict(
        env_file=tuple(f for f in _env_file_candidates if os.path.isfile(f)) or ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton for application settings."""
    return Settings()
