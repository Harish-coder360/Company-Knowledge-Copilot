"""Application configuration and settings."""
from functools import lru_cache
from typing import List, Optional
import os

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openai_api_base: str = Field(default="https://api.openai.com/v1", env="OPENAI_API_BASE")

    vector_db_url: str = Field(default="", env="VECTOR_DB_URL")
    vector_db_path: str = Field(default="./data/chroma", env="VECTOR_DB_PATH")

    allowed_origins: List[str] = Field(default_factory=lambda: ["*"])
    mcp_server_config: Optional[str] = Field(default=None, env="MCP_SERVER_CONFIG")

    chunk_size: int = Field(default=1000)
    chunk_overlap: int = Field(default=200)
    top_k: int = Field(default=4)
    max_context_chars: int = Field(default=6000)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance."""

    return Settings()


settings = get_settings()
